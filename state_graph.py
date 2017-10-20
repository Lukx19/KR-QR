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


def generateNextStates(cur_state):
    next_states = []
    quantities = ['inflow', 'volume']
    category = ['mag', 'der']
    for i in quantities:
        for j in category:
            for k in ['increase', 'decrease']:
                desc = ""
                new_state = copy.deepcopy(cur_state)
                if k == "increase":
                    new_state.state[i][j].increase()
                    desc += i + " " + j + \
                        " increases to " + \
                        new_state.state[i][j].getName() + "\n"
                else:
                    new_state.state[i][j].decrease()
                    desc += i + " " + j + \
                        " decreases to " + \
                        new_state.state[i][j].getName() + '\n'

                # check whether new state is different from previous state
                if new_state.state[i][j].getVal() != cur_state.state[i][j].getVal():

                    # change outflow according to volume
                    if k == "increase" and i == 'volume' and j == 'mag':
                        new_state.state['outflow'][j].increase()
                        desc += "ouflow " + j + "increases to " + \
                                new_state.state['outflow'][j].getName() + '\n'

                    # change outflow according to volume
                    if k == "decrease" and i == 'volume' and j == 'mag':
                        new_state.state['outflow'][j].decrease()
                        desc += "ouflow " + j + "decrease to " + \
                                new_state.state['outflow'][j].getName() + '\n'

                    # changes in derivate can be added without extra check
                    if j == 'der':
                        next_states.append(
                            {'state': new_state, 'change': StateChange(desc)})
                    else:
                        # changes in magnitude can only happen when sign of derivative corresponds
                        if k == "increase" and cur_state.state[i]['der'].getVal() == 1:
                            next_states.append(
                                {'state': new_state, 'change': StateChange(desc)})
                            # print('incr')
                        if k == "decrease" and cur_state.state[i]['der'].getVal() == -1:
                            next_states.append(
                                {'state': new_state, 'change': StateChange(desc)})
                            # print('decr')

    inflow_inverse_states = []
    for state_dict in next_states:
        if state_dict['state'].state['inflow']['mag'] != curr_state.state['inflow']['mag']:
            continue
        negative_state = copy.deepcopy(state_dict)
        negative_state['state'].state['inflow']['der'].increase()
        derivation = negative_state['state'].state['inflow']['der']
        if negative_state['state'] == state_dict['state']:
            derivation.decrease()
            negative_state['change'].desciption += " inflow decresed to " + \
                derivation.getName() + '\n'
        else:
            negative_state['change'].desciption += " inflow increased to " + \
                derivation.getName() + '\n'

        inflow_inverse_states.append(negative_state)
    return next_states + inflow_inverse_states


def printState(state_obj):
    state = state_obj.state
    print(state['inflow']['mag'].getName(), state['inflow']['der'].getName())
    print(state['volume']['mag'].getName(), state['volume']['der'].getName())
    print(state['outflow']['mag'].getName(), state['outflow']['der'].getName())
    print('----------------------')


def addNewState(edges, states, source, target, change):
    source.next_states.append(target)
    edges.append({"explanation": change.desciption,
                  "source": source, "target": target})
    states.append(target)
    return edges, states

# change is a value representing change in derivation of inflow [-1,0,1]


def applyRules(state_obj):
    state = state_obj.state
    # apply assumption: if the volume is on maximum. Its derivative must be zero
    if state['volume']['mag'].getVal() == 2:
        state['volume']['der'].decrease()
        state['outflow']['der'].decrease()
        return True
    # apply derivative on inflow
    if state['inflow']['der'].getVal() == 1 and state['inflow']['mag'].getVal == 0:
        state['inflow']['mag'].increase()
        return True
    # apply influence of inflow on volume
    if state['inflow']['mag'].getVal() == 1 and state['volume']['mag'].getVal() != 1:
        state['volume']['der'].increase()
        # apply proportiality between states
        state['outflow']['der'].setStateAs(state['volume']['der'])
        return True

    if state['volume']['der'] != state['outflow']['der']:
        state['outflow']['der'].setStateAs(state['volume']['der'])
        return True
    return False


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


def isRedundantState(states, state):
    for s in states:
        if s == state:
            return True
    return False


#------------------------------------ VISUALIZATION -------------------------------
# returns the values for all variables in text format
def getStateText(state):
    in_mag = state.state['inflow']['mag'].getName()
    in_der = state.state['inflow']['der'].getName()
    vol_mag = state.state['volume']['mag'].getName()
    vol_der = state.state['volume']['der'].getName()
    out_mag = state.state['outflow']['mag'].getName()
    out_der = state.state['outflow']['der'].getName()
    return in_mag+"  "+in_der+"\n"+vol_mag+"  "+vol_der+"\n"+out_mag+"  "+out_der

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
fringe = queue.LifoQueue()
fringe.put(initial_state)
iteration = 0
while not fringe.empty():
    curr_state = fringe.get(block=False)
    print('start state:')
    printState(curr_state)
    valid_states = []
    for state_dict in generateNextStates(curr_state):
        # printState(state)
        if validateState(state_dict['state']):
            valid_states.append(state_dict)
    for state_dict in valid_states:
        if not applyRules(state_dict['state']):
            print('Not possible to apply rules')
        if not isRedundantState(states, state_dict['state']):
            edges, states = addNewState(
                edges, states, source=curr_state, target=state_dict['state'], change=state_dict['change'])
            fringe.put(state_dict['state'])
            printState(state_dict['state'])

    dot_graph = generateGraph(edges)
    dot_graph.write_png('TEST_graph'+str(iteration)+'.png')
    iteration+=1

    print('*****************************')
    input("Press Enter to continue...")
