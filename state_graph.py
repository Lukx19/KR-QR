import copy
import queue
import pydot


class NZP:
    def __init__(self):
        self.names = ['-', '0', '+']
        self.vals = [-1, 0, 1]
        self.stationary = [False, True, False]


class ZP:
    def __init__(self):
        self.names = ['0', '+']
        self.vals = [0, 1]
        self.stationary = [True, False]


class ZPM:
    def __init__(self):
        self.names = ['0', '+', 'm']
        self.vals = [0, 1, 2]
        self.stationary = [True, False, True]


class QSpace(object):
    def __init__(self, name, Qmodel, state):
        self.name = name
        self.q_model = Qmodel
        self.current_state = state
        self.maximum = len(self.q_model.vals)

    def increase(self):
        if self.current_state < self.maximum - 1:
            self.current_state += 1

    def decrease(self):
        if self.current_state > 0:
            self.current_state -= 1

    def setStateAs(self, q_state):
        # TODO add check if two states are the same
        self.current_state = q_state.current_state

    def getVal(self):
        return self.q_model.vals[self.current_state]

    def getName(self):
        return self.q_model.names[self.current_state]

    def isStationary(self):
        return self.q_model.stationary[self.current_state]

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.getVal() == other.getVal()
        return False

    def __ne__(self, other):
        return not self.__eq__(other)


class State:
    def __init__(self, quantities):
        self.state = {
            'inflow': {'mag': quantities[0],
                       'der': quantities[1]},
            'volume': {'mag': quantities[2],
                       'der': quantities[3]},
            'outflow': {'mag': quantities[4],
                        'der': quantities[5]}
        }
        self.next_states = []
        self.quantities = quantities
        self.name = "0"
        self.desc =""

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            for idx in range(len(self.quantities)):
                if self.quantities[idx] != other.quantities[idx]:
                    return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


class StateChange:
    def __init__(self, desc):
        self.desciption = desc


def stationaryToIntervalChange(state_obj):
    for qt in state_obj.quantities:
        if qt.isStationary():
            return True
    return False


def genFlipedInflow(state_obj):
    states = []
    if state_obj.state['inflow']['der'].getVal() == 0:
        states.append(newState(state_obj,[('inflow','der',+1)],desc="Id+", transition="increase"))
        if state_obj.state['inflow']['mag'].getVal() != 0:
            states.append(newState(state_obj,[('inflow','der',-1)],desc="Id-", transition="decrease"))

        return states

    if (state_obj.state['inflow']['mag'].getVal() == 0
        and state_obj.state['inflow']['der'].getVal() == 1):
        return states
    if (state_obj.state['inflow']['mag'].getVal() == 1
        and state_obj.state['outflow']['der'].getVal() == 0
        and state_obj.state['outflow']['mag'].getVal() != 2):
        return states
    if (state_obj.state['inflow']['der'].getVal() == -1
        and state_obj.state['outflow']['mag'].getVal() == 2):
        return states
    if state_obj.state['inflow']['der'].getVal() == -1:
        states.append(newState(state_obj,[('inflow','der',+1)],desc="Id+", transition="increase"))
        return states
    if state_obj.state['inflow']['der'].getVal() == 1:
        states.append(newState(state_obj,[('inflow','der',-1)],desc="Id-", transition="decrease"))
        return states
    return states

def newState(state_obj,change =[('inflow','der',0)],desc="", transition=""):
    new_state = copy.deepcopy(state_obj)
    for ch in change:
        if ch[2] == -1:
            new_state.state[ch[0]][ch[1]].decrease()
        elif ch[2] == 1:
            new_state.state[ch[0]][ch[1]].increase()

    return {'state': new_state, 'desc':desc, 'transition': transition}

def generateNextStates(state_obj):
    state = state_obj.state
    new_states = []
    # imidiate changes
    if state['outflow']['mag'].getVal() == 0 and state['outflow']['der'].getVal() == 1:
         new_states.append(newState(state_obj,[('volume','mag',1),('outflow','mag',1)],
         desc="Im+->Vd+,Od+", transition="time"))
         new_states[-1]['state'].desc="Positive change in volume/outflow causes increase in magnitude of these  quantities."

    if state['inflow']['mag'].getVal() == 0 and state['inflow']['der'].getVal() == 1:
         changes = [('inflow','mag',1)]
         desc = "Id+->Im+. "
         state_desc = "Positive change in inflow influences magnitude of inflow."
         if state['outflow']['der'].isStationary():
            changes.append(('outflow','der',1))
            changes.append(('volume','der',1))
            state_desc+=" Positive change in inflow magnitude causes to positivelly increase change of volume and outflow."
         new_states.append(newState(state_obj,changes,desc=desc+"Im+->Vd+,Od+", transition="time"))
         new_states[-1]['state'].desc=state_desc

    if len(new_states) == 0:
        new_states = new_states + genFlipedInflow(state_obj)
    # Changes which take long time:

    # increasing inflow volume
    if (state['inflow']['mag'].getVal() == 1 and state['inflow']['der'].getVal() == 1):
        # apply positive Infuence
        if state['outflow']['mag'].getVal() != 2:
            new_states.append(newState(state_obj,[('volume','der',+1),('outflow','der',+1)],
            desc="E+->Vd+,Od+", transition="time"))
            new_states[-1]['state'].desc="Increasing inflow. Increasing derivation of Volume and Outflow."
        if state['outflow']['mag'].getVal() == 1 and state['outflow']['der'].getVal() == 1:
            # go to maximal state
            new_states.append(newState(state_obj,[('volume','mag',1),
                ('volume','der',-1),('outflow','mag',1),('outflow','der',-1)],
                desc="E+->Om+", transition="time"))
            new_states[-1]['state'].desc="Increasing inflow. Maximal capacity of container reached."

        # rate of changes between inflow and outflow- outflow is faster -> go back to steady
        if (state['outflow']['mag'].getVal() == 1
            and state['outflow']['der'].getVal() == state['inflow']['der'].getVal()):
            new_states.append(newState(state_obj,[('volume','der',-1),('outflow','der',-1)],
            desc="Im<Om->Vd-,Od-", transition="time"))
            new_states[-1]['state'].desc="Increasing inflow. Inflow is increasing slower than Outflow. The volume is in positive steady state."

    # steady inflow volume
    if (state['inflow']['mag'].getVal() == 1 and state['inflow']['der'].getVal() == 0):
        change = -1*  state['outflow']['der'].getVal()
        s = '+' if change >0 else '-' if change < 0 else '~'
        new_states.append(newState(state_obj,
            [('volume','der',change),('outflow','der',change)],
            desc="E~->Vd"+s+',Od'+s))
        new_states[-1]['state'].desc="Positive steady inflow."
        if state['outflow']['der'].getVal() == 1:
            new_states.append(newState(state_obj,[('volume','mag',1),
                ('volume','der',-1),('outflow','mag',1),('outflow','der',-1)],
                desc="E~->Vm+,Om+", transition="time"))
            new_states[-1]['state'].desc="Positive steady inflow. Maximal capacity of container reached."

    # decreasing inflow volume
    if (state['inflow']['mag'].getVal() == 1 and state['inflow']['der'].getVal() == -1):
        # apply negative influence
        new_states.append(newState(state_obj,[('volume','der',-1),('outflow','der',-1)],
        desc="E-->Vd-,Od-", transition="time"))
        # extreme no inflow volume left
        if state['outflow']['der'].getVal() == -1 and state['outflow']['mag'].getVal() < 2:
            new_states.append(newState(state_obj,[('inflow','der',+1),('inflow','mag',-1)],
            desc="E-->Id0,Im0", transition="time"))
            new_states[-1]['state'].desc="Inflow is empty."
        # colapsing from maximum to plus
        if state['outflow']['mag'].getVal() == 2 and state['outflow']['der'].getVal() == -1:
            new_states.append(newState(state_obj,[('volume','mag',-1),('outflow','mag',-1)],
            desc="E-->Vm-,Om-", transition="time"))
            new_states[-1]['state'].desc="Inflow is is slowing down what causes increase in outflow rate."
        # speed of decrease can be different in inflow and outflow -> go to steady outflow
        if (state['outflow']['der'].getVal() == state['inflow']['der'].getVal()
            and not state['outflow']['mag'].isStationary()):
            new_states.append(newState(state_obj,[('volume','der',+1),('outflow','der',+1)],
            desc="E-->Vd-,Od-", transition="time"))
            new_states[-1]['state'].desc="Positive steady state"

    # no inflow volume
    if (state['inflow']['mag'].getVal() == 0 and state['inflow']['der'].getVal() == 0):
        if state['outflow']['mag'].getVal() > 0:
            new_states.append(newState(state_obj,[('volume','der',-1),('outflow','der',-1)],
            desc="E0->Vd-,Od-", transition="time"))

        if (state['outflow']['mag'].getVal() == 1 and state['outflow']['der'].getVal() == -1):
            new_states.append(newState(state_obj,[('volume','der',1),('outflow','der',1),
                ('volume','mag',-1),('outflow','mag',-1)], desc="E0->Vd+,Od+", transition="time"))
    # print('new states generated: ',len(new_states))
    return new_states




def printState(state_obj):
    state = state_obj.state
    print(state_obj.name)
    print(state['inflow']['mag'].getName(), state['inflow']['der'].getName())
    print(state['volume']['mag'].getName(), state['volume']['der'].getName())
    print(state['outflow']['mag'].getName(), state['outflow']['der'].getName())
    print('----------------------')

def createEdge(source, target, desc, transition):
    return {"explanation": desc,"source": source, "target": target, "transition": transition}

def addNewState(edges, states, source, target, desc, transition):
    source.next_states.append(target)
    edges.append(createEdge(source,target,desc,transition))
    states.append(target)
    return edges, states


def existingState(states, state):
    for s in states:
        if s == state:
            return s
    return None


#------------------------------------ VISUALIZATION -------------------------------
# returns the values for all variables in text format
def getStateText(state):
    in_mag = state.state['inflow']['mag'].getName()
    in_der = state.state['inflow']['der'].getName()
    vol_mag = state.state['volume']['mag'].getName()
    vol_der = state.state['volume']['der'].getName()
    out_mag = state.state['outflow']['mag'].getName()
    out_der = state.state['outflow']['der'].getName()
    return str(state.name)+'\n'+in_mag+"  "+in_der+"\n"+vol_mag+"  "+vol_der+"\n"+out_mag+"  "+out_der

# generates a visual (directed) graph of all states
def generateGraph(edgeList):
    graph = pydot.Dot(graph_type='digraph', center=True, size=15)
    for edgeObj in edgeList:
        transitionText = edgeObj['explanation'] # explanation for transition
        transitionType = edgeObj['transition']  # type of transition (+, -, or time)
        sourceState = edgeObj['source']         # source state (obj)
        targetState = edgeObj['target']         # target state (obj)

        if transitionType == "increase":
            edgeFillColor = '#00FF00'
        elif transitionType == "decrease":
            edgeFillColor = '#FF0000'
        else:
            edgeFillColor = '#black'

        sourceStateText = getStateText(sourceState) # all values of source state in text format
        targetStateText = getStateText(targetState) # all values of target state in text format

        if len(targetState.next_states) == 0:
            nodeFillColor = '#81B2E0'
            nodeBorder = 2.8
        else:
            nodeFillColor = '#92E0DF'
            nodeBorder = 1.5

        sourceNode = pydot.Node(sourceStateText, shape='rectangle',
            style="filled", fillcolor='#92E0DF', penwidth=1.5)
        graph.add_node(sourceNode)

        targetNode = pydot.Node(targetStateText, shape='rectangle',
            style="filled", fillcolor=nodeFillColor, penwidth=nodeBorder)
        graph.add_node(targetNode)

        edge = pydot.Edge(sourceNode, targetNode, label=transitionText,
            color=edgeFillColor, penwidth=2.25)
        graph.add_edge(edge)

    return graph

def decodeDesc(desc):
    out = desc.replace('d',"derivative] ")
    out = out.replace('m',"magnitude] ")
    out = out.replace('I',"[Inflow ")
    out = out.replace('E+',"Inflow is increasing ")
    out = out.replace('E-',"Inflow is decreasing ")
    out = out.replace('E~',"Inflow is positive ")
    out = out.replace('E0',"Inflow is closed ")

    out = out.replace(',',"and ")
    out = out.replace('->',"implies that ")
    out = out.replace('O',"[Outflow ")
    out = out.replace('V',"[Volume ")
    out = out.replace('+',"increases ")
    out = out.replace('-',"decreases ")
    # out = out.replace('~',"is steady ")
    out = out.replace('<',"is less than ")
    out = out.replace('.',"\n ")


    return out
def printIntraState(state_obj):
    state = state_obj.state
    printState(state_obj)
    print(state_obj.desc)
    # if state['inflow']['der'].getVal() == 1:
    #     print('Inflow is increasing')
    # if state['inflow']['der'].getVal() == -1:
    #     print('Inflow is decreasing')
    # if state['inflow']['der'].getVal() == 0 and state['inflow']['mag'].getVal() == 0:
    #     print('Inflow is positive without change')
    # if state['outflow']['mag'].getVal() == 2:
    #     print('Container is full.')
    # if state['outflow']['der'].getVal() == 1:
    #     print('')
    print('----------------------')

def printInterstate(name_a,name_b,desc):
    print("{:<3}->{:<3}:{:<30}{:<100}".format(name_a,name_b,desc,decodeDesc(desc)))
# --------------------------------------- MAIN --------------------------------------
inflow_mag = QSpace('inflow_mag', ZP(), 0)
inflow_der = QSpace('inflow_der', NZP(), 1)
volume_mag = QSpace('volume_mag', ZPM(), 0)
volume_der = QSpace('volume_der', NZP(), 1)
outflow_mag = QSpace('outflow_mag', ZPM(), 0)
outflow_der = QSpace('outflow_der', NZP(), 1)

initial_state = State(
    [inflow_mag, inflow_der,
     volume_mag, volume_der,
     outflow_mag, outflow_der])

states = [initial_state]
edges = []
fringe = queue.Queue()
fringe.put(initial_state)
iteration = 0

dot_graph = None
while not fringe.empty():
    curr_state = fringe.get(block=False)
    new_states = generateNextStates(curr_state)
    for state_dict in new_states:
        same_state = existingState(states, state_dict['state'])
        if same_state is None:
            state_dict['state'].name = str(len(states))
            edges, states = addNewState(edges, states,
                            source=curr_state, target=state_dict['state'],
                            desc=state_dict['desc'],transition=state_dict['transition'])
            fringe.put(state_dict['state'])
            printInterstate(curr_state.name,state_dict['state'].name,state_dict['desc'])
        elif curr_state != same_state:
            curr_state.next_states.append(same_state)
            edges.append(createEdge(source=curr_state, target=same_state,
                                    desc=state_dict['desc'], transition=state_dict['transition']))
            printInterstate(curr_state.name,same_state.name,state_dict['desc'])

    dot_graph = generateGraph(edges)
    iteration+=1

    # print('************'+str(iteration)+'*****************')
    # input("Press Enter to continue...")
dot_graph.write('graph.dot')
dot_graph.write_png('TEST_graph.png')
for st in states:
    printIntraState(st)