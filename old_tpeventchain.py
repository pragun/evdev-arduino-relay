# This keeps track of the timestamps for when the last
# finger on/off event happened

from touchpadstate import TouchPadState
from collections import deque
from tabulate import tabulate

max_history = 20
max_fingers = 5

class TPEventChain(object):
    def __init__(self):
        self.last_number_of_fingers = 0
        self.tap_chain = deque([(0,0.0) for i in range(max_history)],maxlen=max_history)

    def update_state(self,cts):
        if self.last_number_of_fingers != cts.number_of_active_touch:
            self.tap_chain.appendleft((cts.number_of_active_touch,cts.timestamp))
            self.last_number_of_fingers = cts.number_of_active_touch
            return True
        else:
            return False
            
    #calculate timing    
    def __repr__(self):
        a = []
        for i in range(max_history + 1):
            a.append(i for i in self.tap_chain)
        return tabulate(self.tap_chain,floatfmt=".4f")

if __name__ == '__main__':
    a = TPEventChain()
    print(str(a))

    
