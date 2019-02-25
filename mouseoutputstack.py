#From the chain of taps on the touchpad,
#this will check if the timing indeed matches what
#it needs to be for a single tap, double tap, etc
#after that it will create an event in the event queue

from config import tap_timings
from sendusbevents import SendUsbEvents

def FourMouse(a):
    print("FourMouse")
    
def ThreeMouse(a):
    print("ThreeMouse")

def FiveMouse(a):
    print("FiveMouse")

class MouseOutputStack(object):
    def __init__(self):
        self.drag_active = False

    #Expected of this event to return a list of mouse events to be output
    def check_for_event(self,cts):
        if cts.tracking_id_flag:
            return self.tracking_id_event(cts)
        if cts.movement_flag:
            return self.movement_event(cts)
            
    def movement_event(self,cts):
        a = self.check_n_tap_movement(cts)
        if a is not None:
            (n,delx,dely) = a
            print(a)
            if n == 1:
                return [('move_mouse',int(delx),int(dely))]
            if n == 2:
                return [('scroll_mouse',int(delx),int(dely))]
            if n == 3:
                if self.drag_active:
                    return [('move_mouse',int(delx),int(dely))]
                else:
                    self.drag_active = True
                    return [('press_button',1,),\
                    ('move_mouse',int(delx),int(dely))]

            if n == 4:
                return [('four_mouse',)]
            
            if n == 5:
                return [('five_mouse',)]
            
        
    #Helper method does not return events
    def check_n_tap_movement(self,cts):
        cts2 = cts.last_touchpad_state
        n = cts.number_of_active_touch
        if (n > 0) \
           and (cts2 != None) \
           and (cts2.number_of_active_touch == n) \
           and (cts.tap_chain[0][0] == n):
            time_delta = 1000*(cts.timestamp - cts.tap_chain[0][1])
            if time_delta > tap_timings[n]:
                delx = cts.centroid_x - cts2.centroid_x
                dely = cts.centroid_y - cts2.centroid_y
                return (n,delx,dely)
            #Make sure that the number of touches is the same as it was

    #Does return events
    def tracking_id_event(self,cts):
        if self.drag_active:
            self.drag_active = False
            return [('release_button',1,)]
        
        a = self.check_for_tap_event(cts) 
        if a:
            return [a]
        
    #Helper Function
    def check_for_tap_event(self,cts):
        if cts.number_of_active_touch == 0:
            max_tap = 0
            end_chain = 0
            list_tap_chain = list(cts.tap_chain)[1:] #Here we take the
            #first element out because, the for loop is going to look for
            #the last time there were no fingers on the touchpad.
            #But since the first element [by the start condition]
            #is also that we remove it so the for loop can find the
            #last time there were no fingers on the touchpad
        
            for i,(n,t) in enumerate(list_tap_chain):
                max_tap = max(max_tap,n)
                if n == 0:
                    start_chain = i-1
                    #print("Found start of previous event chain at %f, index:%d"%(t,i))
                    #print("MaxTap:%d"%max_tap)
                    break            
                
            start_timestamp = list_tap_chain[start_chain][1]
            delta_t = cts.timestamp-start_timestamp
            delta_t *= 1000
            print("Gesture Length: %f, Num:%d"%(delta_t,max_tap))
            if delta_t < tap_timings[max_tap]:
                return ('tap_click', max_tap)
            #This is a good gesture! Let us report an event


