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
        self.names = ['zero', 'plus']
        self.vals = [0, 1]
        self.stationary = [True, False]


class ZPM:
    def __init__(self):
        self.names = ['zero', 'plus', 'max']
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
        self.name = "noname"

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
        inc_state = copy.deepcopy(state_obj)
        inc_state.state['inflow']['der'].increase()
        states.append({'state': inc_state, 'change': StateChange(desc="Im+"), 'transition': "increase"})
        if state_obj.state['inflow']['mag'].getVal() != 0:
            dec_state = copy.deepcopy(state_obj)
            dec_state.state['inflow']['der'].decrease()
            states.append(
                {'state': dec_state, 'change': StateChange(desc="Im-"), 'transition': "decrease"})
        return states
    if stationaryToIntervalChange(state_obj):
        return states
    # if (state_obj.state['inflow']['mag'].getVal() == 0
    #     or state_obj.state['outflow']['der'].getVal() == 0):
    #     return states
    if state_obj.state['inflow']['der'].getVal() == -1:
        inc_state = copy.deepcopy(state_obj)
        inc_state.state['inflow']['der'].increase()
        states.append({'state': inc_state, 'change': StateChange(desc="Im+"), 'transition': "increase"})
        return states
    if state_obj.state['inflow']['der'].getVal() == 1:
        dec_state = copy.deepcopy(state_obj)
        dec_state.state['inflow']['der'].decrease()
        states.append({'state': dec_state, 'change': StateChange(desc="Im-"), 'transition': "decrease"})
        return states
    return states

def newState(state_obj,change =[('inflow','der',0)],desc="", transition=""):
    new_state = copy.deepcopy(state_obj)
    for ch in change:
        if ch[2] == -1:
            new_state.state[ch[0]][ch[1]].decrease()
        elif ch[2] == 1:
            new_state.state[ch[0]][ch[1]].increase()

    return {'state': new_state, 'change': StateChange(desc=desc), 'transition': transition}

def generateNextStates(state_obj):
    state = state_obj.state
    new_states = []
    # imidiate changes
    if state['outflow']['mag'].getVal() == 0 and state['outflow']['der'].getVal() == 1:
         new_states.append(newState(state_obj,[('volume','mag',1),('outflow','mag',1)],
         desc="IM1", transition="time"))

    if state['inflow']['mag'].getVal() == 0 and state['inflow']['der'].getVal() == 1:
         new_states.append(newState(state_obj,[('inflow','mag',1),
            ('outflow','der',1),('volume','der',1)],
            desc="IM2", transition="time"))


    # Changes which take long time:

    # increasing inflow volume
    if (state['inflow']['mag'].getVal() == 1 and state['inflow']['der'].getVal() == 1):
        # apply positive Infuence
        if state['outflow']['mag'].getVal() != 2:
            new_states.append(newState(state_obj,[('volume','der',+1),('outflow','der',+1)],
            desc="", transition="time")) #TODO add descr
        if state['outflow']['mag'].getVal() == 1 and state['outflow']['der'].getVal() == 1:
            # go to maximal state
            new_states.append(newState(state_obj,[('volume','mag',1),
                ('volume','der',-1),('outflow','mag',1),('outflow','der',-1)],
                desc="", transition="time")) #TODO add descr
        # # apply derivatives to increase volume magnitude
        # if state['outflow']['mag'].getVal() == 0 and state['outflow']['der'].getVal() == 1:
        #     new_states.append(newState(state_obj,[('volume','mag',+1),('outflow','mag',+1)]))

        # rate of changes between inflow and outflow- outflow is faster -> go back to steady
        if (state['outflow']['mag'].getVal() == 1
            and state['outflow']['der'].getVal() == state['inflow']['der'].getVal()):
            new_states.append(newState(state_obj,[('volume','der',-1),('outflow','der',-1)],
            desc="steady", transition="time"))

    # steady inflow volume
    if (state['inflow']['mag'].getVal() == 1 and state['inflow']['der'].getVal() == 0):
        change = -1*  state['outflow']['der'].getVal()
        new_states.append(newState(state_obj,[('volume','der',change),('outflow','der',change)]))
        if state['outflow']['der'].getVal() == 1:
            new_states.append(newState(state_obj,[('volume','mag',1),
                ('volume','der',-1),('outflow','mag',1),('outflow','der',-1)],
                desc="", transition="time")) #TODO add descr

    # decreasing inflow volume
    if (state['inflow']['mag'].getVal() == 1 and state['inflow']['der'].getVal() == -1):
        # apply negative influence
        new_states.append(newState(state_obj,[('volume','der',-1),('outflow','der',-1)],
        desc="d1", transition="time"))
        # extreme no inflow volume left
        if state['outflow']['der'].getVal() == -1 and state['outflow']['mag'].getVal() < 2:
            new_states.append(newState(state_obj,[('inflow','der',+1),('inflow','mag',-1)],
            desc="d2", transition="time"))
        # colapsing from maximum to plus
        if state['outflow']['mag'].getVal() == 2 and state['outflow']['der'].getVal() == -1:
            new_states.append(newState(state_obj,[('volume','mag',-1),('outflow','mag',-1)],
            desc="d3", transition="time"))
        # speed of decrease can be different in inflow and outflow -> go to steady outflow
        if state['outflow']['der'].getVal() == state['inflow']['der'].getVal():
            new_states.append(newState(state_obj,[('volume','der',+1),('outflow','der',+1)],
            desc="d3", transition="time"))

    # no inflow volume
    if (state['inflow']['mag'].getVal() == 0 and state['inflow']['der'].getVal() == 0):
        if state['outflow']['mag'].getVal() > 0:
            new_states.append(newState(state_obj,[('volume','der',-1),('outflow','der',-1)],
            desc="", transition="time")) #TODO add descr
        if (state['outflow']['mag'].getVal() == 1 and state['outflow']['der'].getVal() == -1):
            new_states.append(newState(state_obj,[('volume','der',1),('outflow','der',1),
                ('volume','mag',-1),('outflow','mag',-1)], desc="", transition="time")) #TODO add descr

    new_states = new_states + genFlipedInflow(state_obj)
    print('new states generated: ',len(new_states))
    return new_states




def printState(state_obj):
    state = state_obj.state
    print(state['inflow']['mag'].getName(), state['inflow']['der'].getName())
    print(state['volume']['mag'].getName(), state['volume']['der'].getName())
    print(state['outflow']['mag'].getName(), state['outflow']['der'].getName())
    print('----------------------')

def createEdge(source, target, change, transition):
    return {"explanation": change.desciption,"source": source, "target": target, "transition": transition}

def addNewState(edges, states, source, target, change, transition):
    source.next_states.append(target)
    edges.append(createEdge(source,target,change,transition))
    states.append(target)
    return edges, states


# -------------------------------------QR allgorithm helpers ---------------------

def validateState(state_obj):
    state = state_obj.state
    # return True
    # volume/outflow derivation cannot be positive when the container is full
    if (state['volume']['mag'].getVal() == 2 and state['volume']['der'].getVal() == 1):
        return False
    # decreasing volume or oytflow is not possible when there is no quantity
    if (state['volume']['mag'].getVal() == 0 and state['volume']['der'].getVal() == -1):
        return False
    if (state['outflow']['mag'].getVal() == 0 and state['outflow']['der'].getVal() == -1):
        return False
    # increasing derivation of volume is not possible when there is no inflow volume
    if (state['inflow']['mag'].getVal() == 0 and state['volume']['der'].getVal() == 1):
        return False
    if (state['inflow']['der'].getVal() == -1 and state['inflow']['mag'].getVal() == 0):
        return False
    return True


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

# --------------------------------------- MAIN --------------------------------------
inflow_mag = QSpace('inflow_mag', ZP(), 0)
inflow_der = QSpace('inflow_der', NZP(), 2)
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
fringe = queue.LifoQueue()
fringe.put(initial_state)
iteration = 0


while not fringe.empty():
    curr_state = fringe.get(block=False)
    print('start state:')
    printState(curr_state)
    new_states = generateNextStates(curr_state)
    for state_dict in new_states:
        # if not validateState(state_dict['state']):
        #     continue
        same_state = existingState(states, state_dict['state'])
        if same_state is None:
            print("NONE")
            state_dict['state'].name = str(len(states))
            edges, states = addNewState(edges, states,
                            source=curr_state, target=state_dict['state'],
                            change=state_dict['change'],transition=state_dict['transition'])
            fringe.put(state_dict['state'])
            printState(state_dict['state'])
        elif curr_state != same_state:
            print ("aaaaaaaaaaaaaa")
            curr_state.next_states.append(same_state)
            edges.append(createEdge(source=curr_state, target=same_state,
                                    change=state_dict['change'], transition=state_dict['transition']))
            printState(state_dict['state'])
    dot_graph = generateGraph(edges)
    dot_graph.write_png('TEST_graph'+str(iteration)+'.png')
    iteration+=1

    print('************'+str(iteration)+'*****************')
    # input("Press Enter to continue...")