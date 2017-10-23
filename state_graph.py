import copy
import queue
import pydot


class NZP:
    def __init__(self):
        self.names = ['negative', 'zero', 'positive']
        self.vals = [-1, 0, 1]
        self.stationary = [False, True, False]


class ZP:
    def __init__(self):
        self.names = ['zero', 'plus']
        self.vals = [0, 1]
        self.stationary = [True, False]


class ZPM:
    def __init__(self):
        self.names = ['zero', 'plus', 'maximum']
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
    def __init__(self,quantities):
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
        self.name ="noname"

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
        states.append({'state': inc_state, 'change': StateChange(desc = "Im+")})
        if state_obj.state['inflow']['mag'].getVal() != 0:
            dec_state = copy.deepcopy(state_obj)
            dec_state.state['inflow']['der'].decrease()
            states.append({'state': dec_state, 'change': StateChange(desc = "Im-")})
        return states
    if stationaryToIntervalChange(state_obj):
        return states
    if state_obj.state['inflow']['der'].getVal() == -1:
        inc_state = copy.deepcopy(state_obj)
        inc_state.state['inflow']['der'].increase()
        states.append({'state': inc_state, 'change': StateChange(desc = "Im+")})
        return states
    if state_obj.state['inflow']['der'].getVal() == 1:
        dec_state = copy.deepcopy(state_obj)
        dec_state.state['inflow']['der'].decrease()
        states.append({'state': dec_state, 'change': StateChange(desc = "Im-")})
        return states
    return states

def generateNextStates(state_obj):
    state = state_obj.state
    new_states = []
    # getting to maximum
    if state['volume']['der'].getVal() == 1 and state['volume']['mag'].getVal() == 1:
        new = copy.deepcopy(state_obj)
        new.state['volume']['der'].decrease()
        new.state['outflow']['der'].decrease()
        new.state['volume']['mag'].increase()
        new.state['outflow']['mag'].increase()
        desc = "Vm+, Om+"
        new_states.append({'state': new, 'change': StateChange(desc = desc)})

    # apply derivation on inflow magnitude
    if state['inflow']['der'].getVal() == 1:
        new = copy.deepcopy(state_obj)
        new.state['inflow']['mag'].increase()
        new.state['volume']['der'].increase()
        new.state['outflow']['der'].increase()
        desc = "Id+ -> Im+, Vd+, Od+"
        new_states.append({'state': new, 'change': StateChange(desc = desc)})

    # apply influenc of inflow magnitude
    if state['inflow']['mag'].getVal() == 1 and state['volume']['mag'].getVal() < 1:
        new = copy.deepcopy(state_obj)
        new.state['volume']['der'].increase()
        new.state['outflow']['der'].increase()
        desc = "Vd+, Od+"
        new_states.append({'state': new, 'change': StateChange(desc = desc)})

    # # apply influenc of slowing inflow
    # if state['inflow']['der'].getVal() == -1:
    #     new = copy.deepcopy(state_obj)
    #     new.state['volume']['der'].decrease()
    #     new.state['outflow']['der'].decrease()
    #     desc = "Vd-, Od-"
    #     new_states.append({'state': new, 'change': StateChange(desc = desc)})

    # apply influence of steady inflow
    if (state['inflow']['der'].getVal() == 0
        and state['volume']['der'].getVal() == 1
        and state['inflow']['mag'].getVal() == 0):

        new = copy.deepcopy(state_obj)
        new.state['volume']['der'].decrease()
        new.state['outflow']['der'].decrease()
        desc = "Vd-, Od-"
        new_states.append({'state': new, 'change': StateChange(desc = desc)})
    # apply derivatives of increasing volume
    if state['volume']['der'].getVal() == 1 and state['volume']['mag'].getVal() == 0:
        new = copy.deepcopy(state_obj)
        new.state['volume']['mag'].increase()
        new.state['outflow']['mag'].increase()
        desc = "Vd+ Od+ -> Vm+, Om+"
        new_states.append({'state': new, 'change': StateChange(desc = desc)})
    print('generated states',len(new_states))

    # for s in new_states:
    #     state = s['state'].state
    #     if state['inflow']['der'].getVal() == 0:

    #     elif  state['inflow']['der'].getVal() > 0:
    #     else:

    # if len(new_states) == 0:
    new_states = new_states + genFlipedInflow(state_obj)
    return new_states




def printState(state_obj):
    state = state_obj.state
    print(state['inflow']['mag'].getName(), state['inflow']['der'].getName())
    print(state['volume']['mag'].getName(), state['volume']['der'].getName())
    print(state['outflow']['mag'].getName(), state['outflow']['der'].getName())
    print('----------------------')

def createEdge(source, target, change):
    return {"explanation": change.desciption,"source": source, "target": target}

def addNewState(edges, states, source, target, change):
    source.next_states.append(target)
    edges.append(createEdge(source,target,change))
    states.append(target)
    return edges, states


# -------------------------------------QR allgorithm helpers ---------------------

def validateState(state_obj):
    state = state_obj.state
    # correspondence between magnitude of outflow and volume
    # if (state['volume']['der'] != state['outflow']['der']):
    #     return False
    # proportiality is not possible to apply derivatives have different signs
    if (state['volume']['der'].getVal() + state['outflow']['der'].getVal() == 0
        and state['volume']['der'].getVal() != 0
            and state['outflow']['der'].getVal() != 0):
        return False
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
    graph = pydot.Dot(graph_type='digraph')
    for edgeObj in edgeList:
        transitionText = edgeObj['explanation']
        sourceState = edgeObj['source']
        targetState = edgeObj['target']

        sourceStateText = getStateText(sourceState)
        targetStateText = getStateText(targetState)

        sourceNode = pydot.Node(sourceStateText, shape=nodeShape,
            style=nodeStyle, fillcolor=nodeFillColor, color=nodeTextColor)
        graph.add_node(sourceNode)

        if len(targetState.next_states) ==0:
            targetNode = pydot.Node(targetStateText, shape=nodeShape,
                style=nodeStyle, fillcolor='#D0563A', color=nodeTextColor)
        else:
            targetNode = pydot.Node(targetStateText, shape=nodeShape,
                style=nodeStyle, fillcolor=nodeFillColor, color=nodeTextColor)
        graph.add_node(targetNode)

        edge = pydot.Edge(sourceNode, targetNode, label=transitionText,
            labelfontcolor=edgeFillColor, fontsize=edgeFontSize, color=edgeTextColor)
        graph.add_edge(edge)

    #graph.write_png('TEST_graph.png')
    return graph

# --------------------------------------- MAIN --------------------------------------
# general properties
nodeShape = 'rectangle'
nodeStyle = 'filled'
nodeFillColor = '#99DDDF'
nodeTextColor = 'black'
edgeFillColor = 'black'
edgeTextColor = 'black'
edgeFontSize = '12.0'

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


while not fringe.empty():
    curr_state = fringe.get(block=False)
    print('start state:')
    printState(curr_state)
    new_states = generateNextStates(curr_state)
    for state_dict in new_states:
        if not validateState(state_dict['state']):
            continue
        same_state = existingState(states, state_dict['state'])
        if same_state is None:
            print("NONE")
            state_dict['state'].name = str(len(states))
            edges, states = addNewState(edges, states,
                            source=curr_state, target=state_dict['state'], change=state_dict['change'])
            fringe.put(state_dict['state'])
            printState(state_dict['state'])
        elif curr_state != same_state:
            print ("aaaaaaaaaaaaaa")
            curr_state.next_states.append(same_state)
            edges.append(createEdge(source=curr_state, target=same_state,change=state_dict['change']))
            printState(state_dict['state'])
    dot_graph = generateGraph(edges)
    dot_graph.write_png('TEST_graph'+str(iteration)+'.png')
    iteration+=1

    print('************'+str(iteration)+'*****************')
    input("Press Enter to continue...")
