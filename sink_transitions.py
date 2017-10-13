# implementation of pytransitions for the inflow-volume-outflow of a sink with water
# link to pytransitionson github: https://github.com/pytransitions/transitions#quickstart

from transitions import Machine
import random

derivative_states = ['negative', 'zero', 'positive'] # define all possible states for derivatives

class InflowMagnitude(object):
    
    states = ['zero', 'positive'] # define all possible states for magnitude
    
    def __init__(self):

        # initialize state machine
        self.machine = Machine(model=self, states=InflowMagnitude.states, initial='zero')
    
        # add transitions
        self.machine.add_transition(trigger='increase', source='zero', dest='positive')
        self.machine.add_transition(trigger='decrease', source='positive', dest='zero')
        
class InflowDerivative(object):
    
    def __init__(self):

        # initialize state machine
        self.machine = Machine(model=self, states=InflowDerivative.derivative_states, initial='zero')
    
        # add transitions
        self.machine.add_transition(trigger='increase', source='negative', dest='zero')
        self.machine.add_transition(trigger='increase', source='zero', dest='positive')
        self.machine.add_transition(trigger='decrease', source='positive', dest='zero')
        self.machine.add_transition(trigger='decrease', source='zero', dest='negative')
     
        
class VolumeMagnitude(object):
    
    states = ['zero', 'positive', 'maximum'] # define all possible states for magnitude
    
    def __init__(self):

        # initialize state machine
        self.machine = Machine(model=self, states=VolumeMagnitude.states, initial='zero')
    
        # add transitions
        self.machine.add_transition(trigger='increase', source='zero', dest='positive')
        self.machine.add_transition(trigger='increase', source='positive', dest='maximum')
        self.machine.add_transition(trigger='decrease', source='maximum', dest='positive')
        self.machine.add_transition(trigger='decrease', source='positive', dest='zero')
        
class VolumeDerivative(object):
    
    def __init__(self):

        # initialize state machine
        self.machine = Machine(model=self, states=VolumeDerivative.derivative_states, initial='zero')
    
        # add transitions
        self.machine.add_transition(trigger='increase', source='negative', dest='zero')
        self.machine.add_transition(trigger='increase', source='zero', dest='positive')
        self.machine.add_transition(trigger='decrease', source='positive', dest='zero')
        self.machine.add_transition(trigger='decrease', source='zero', dest='negative')
        

class OutflowMagnitude(object):
    
    states = ['zero', 'positive', 'maximum'] # define all possible states for magnitude

    def __init__(self):

        # initialize state machine
        self.machine = Machine(model=self, states=OutflowMagnitude.states, initial='zero')
    
        # add transitions
        self.machine.add_transition(trigger='increase', source='zero', dest='positive')
        self.machine.add_transition(trigger='increase', source='positive', dest='maximum')
        self.machine.add_transition(trigger='decrease', source='maximum', dest='positive')
        self.machine.add_transition(trigger='decrease', source='positive', dest='zero')
        
class OutflowDerivative(object):
    
    def __init__(self):

        # initialize state machine
        self.machine = Machine(model=self, states=OutflowDerivative.derivative_states, initial='zero')
    
        # add transitions
        self.machine.add_transition(trigger='increase', source='negative', dest='zero')
        self.machine.add_transition(trigger='increase', source='zero', dest='positive')
        self.machine.add_transition(trigger='decrease', source='positive', dest='zero')
        self.machine.add_transition(trigger='decrease', source='zero', dest='negative')
  
        
# TEST
print("Define inflow magnitude:")
inflow = InflowMagnitude()
print(inflow.state, "\n")
print("Increase inflow magnitude:")
inflow.increase()
print(inflow.state, "\n")
print("Decrease inflow magnitude:")
inflow.decrease()
print(inflow.state, "\n")