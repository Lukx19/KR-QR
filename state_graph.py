
class NZP:
    def __init__(self):
        self.names = ['negative', 'zero', 'positive']
        self.vals = [-1, 0, 1]
        self.stationary = [False, True, False]


class ZP:
    def __init__(self):
        self.names = ['zero', 'positive']
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
        self.minimum = [e.value for e in self.states][0]
        self.isStationary = False

    def increase(self):
        if self.current_state < self.maximum:
            self.current_state += 1

    def decrease(self):
        if self.current_state > 0:
            self.current_state -= 1

    def getVal(self):
        return self.q_model.vals[self.current_state]

    def getName(self):
        return self.q_model.names[self.current_state]

    def isStationary(self):
        return self.q_model.stationary[self.current_state]


QSpace( 'inflow_mag',NZP(), 1)

class State:
    def __init__(self, quantities):
        self.state = {}
        self.nextStates = []
        self.quantities = quantities


def generateNextStates(current_state)
#return array of all possible states

def connectStates(stateA, stateB):
    stateA.nextStates += stateB

# change is a value representing change in derivation of inflow [-1,0,1]


def generateStates(model, state, change=0):
    newStates = []

    # if change == 0:
    #     # apply derivatives
    #     for qty in model.rules:
    #         if qty.name != model.exogenous:
    #         	# apply derivative


model = {
    'exogenous': 'inflow',
    'rules':
    [
        {
            'name': 'inflow',
            'magnitude': 1,
            'derivations': 1,
            'relations': [[1, 'magnitude', 'volume', 'derivations']]
        },
        {
            'name': 'volume',
            'magnitude': 1,
            'derivations': 1,
            'relations': [[1, 'derivations', 'outflow', 'derivations']]
        }
    ]
}

startState = {'inflow':
              {
                  'magnitude': 1,
                  'derivations': 1,
                  'relations': [[1, 'magnitude', 'volume', 'derivations']]
              },
              'volume':
              {
                  'magnitude': 1,
                  'derivations': 1,
                  'relations': [[1, 'derivations', 'outflow', 'derivations']]
              }}
