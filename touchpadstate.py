from fingerposition import FingerPosition
from collections import deque
from tabulate import tabulate

max_history = 7
max_fingers = 5

class TouchPadState(object):
    def __init__(self):
        self.number_of_active_touch = 0
        #Number of active touches at the last syn report
        self.slots = [FingerPosition(i) for i in range(5)]
        self.timestamp = None
        self.last_number_of_fingers = 0
        self.tap_chain = deque([(0,0.0) for i in range(max_history)],maxlen=max_history)
        self.last_touchpad_state = None
        
    def update_internal_state_syn_report(self):
        self.number_of_active_touch = sum([i.touch for i in self.slots])
        self.update_tap_chain()

    def save_last_state(self):
        #print("here")
        self.last_touchpad_state = TouchPadState.simple_copy(self)
        #print(self.last_touchpad_state)
        
    @classmethod
    def simple_copy(cls,i): #i, is the TouchPadState object to create a deepcopy of
        # In most usage, i would be a MT_Handler type class that inherits
        # TouchPadState
        
        a = cls()
        a.number_of_active_touch = i.number_of_active_touch
        a.slots = [FingerPosition.copy(j) for j in i.slots]
        a.timestamp = i.timestamp
        return a
    
    def distance_moved(self,tp_other):
        pass

    
    def update_tap_chain(self):
        if self.last_number_of_fingers != self.number_of_active_touch:
            self.tap_chain.appendleft((self.number_of_active_touch,self.timestamp))
            self.last_number_of_fingers = self.number_of_active_touch
            return True
        else:
            return False
             
    def __repr_tap_chain__(self):
        a = []
        for i in range(max_history + 1):
            a.append(i for i in self.tap_chain)
        return tabulate(self.tap_chain,floatfmt=".4f")

