import evdev, asyncio, os
import datetime

from evdev_helper import get_apple_touchpad
from fingerposition import FingerPosition
from touchpadstate import TouchPadState
from tapevents import check_for_tap_event
from singletapmovement import check_single_tap_movement
from sendusbevents import SendUsbEvents
#1. Expects a SYN_REPORT between two touch events
#2. If there are more than one fingers on the pad MT_SLOT is reported,
#   otherwise, it doesn't report MT_SLOT

class MT_Handler(TouchPadState):
    def __init__(self,output_event_queue):
        super().__init__()
        
        #The following variables hold state variables
        #for understanding sequential events
        self.output_event_queue = output_event_queue
        self.slot_for_next_report = 0
        self.tracking_id_flag = 0
        self.movement_flag = 0
        self.event_list = []
        #This Flag is set when there is a change in the number of tracking ids
        
        self.handler_dict_abs = {
            evdev.ecodes.ABS_MT_SLOT		:self.abs_mt_slot,		
            evdev.ecodes.ABS_MT_TOUCH_MAJOR	:self.abs_mt_touch_major,	
            evdev.ecodes.ABS_MT_TOUCH_MINOR	:self.abs_mt_touch_minor,	
            evdev.ecodes.ABS_MT_WIDTH_MAJOR	:self.abs_mt_width_major,	
            evdev.ecodes.ABS_MT_WIDTH_MINOR	:self.abs_mt_width_minor,	
            evdev.ecodes.ABS_MT_ORIENTATION	:self.abs_mt_orientation,	
            evdev.ecodes.ABS_MT_POSITION_X	:self.abs_mt_position_x	,
            evdev.ecodes.ABS_MT_POSITION_Y	:self.abs_mt_position_y	,
            evdev.ecodes.ABS_MT_TOOL_TYPE	:self.abs_mt_tool_type	,
            evdev.ecodes.ABS_MT_BLOB_ID	        :self.abs_mt_blob_id	,	
            evdev.ecodes.ABS_MT_TRACKING_ID	:self.abs_mt_tracking_id,	
            evdev.ecodes.ABS_MT_PRESSURE	:self.abs_mt_pressure	,	
            evdev.ecodes.ABS_MT_DISTANCE	:self.abs_mt_distance	,	
            evdev.ecodes.ABS_MT_TOOL_X	        :self.abs_mt_tool_x	,	
            evdev.ecodes.ABS_MT_TOOL_Y	        :self.abs_mt_tool_y	,

            evdev.ecodes.ABS_X                  :self.abs_x,
            evdev.ecodes.ABS_Y                  :self.abs_y,
            evdev.ecodes.ABS_Z                  :self.abs_z,
            evdev.ecodes.ABS_PRESSURE           :self.abs_pressure,
            evdev.ecodes.ABS_TOOL_WIDTH         :self.abs_tool_width,
        }

        self.handler_dict_syn = {
            evdev.ecodes.SYN_REPORT             :self.syn_report,
        }

        self.handler_dict_key = {
            evdev.ecodes.BTN_TOOL_QUINTTAP	:self.btn_tool_quinttap,	
            evdev.ecodes.BTN_TOUCH		:self.btn_touch,		
            evdev.ecodes.BTN_TOOL_DOUBLETAP	:self.btn_tool_doubletap,
            evdev.ecodes.BTN_TOOL_TRIPLETAP	:self.btn_tool_tripletap,
            evdev.ecodes.BTN_TOOL_QUADTAP	:self.btn_tool_quadtap,
            evdev.ecodes.BTN_TOOL_FINGER        :self.btn_tool_finger,
        }

        self.handler_dict = {
            evdev.ecodes.EV_SYN : self.handler_dict_syn,
            evdev.ecodes.EV_KEY : self.handler_dict_key,
            evdev.ecodes.EV_ABS : self.handler_dict_abs,
        }


    def process_event(self,event):
        self.handler_dict[event.type][event.code](event)
        
    def __repr__(self):
        slot_text = '\n'.join([str(i) for i in self.slots])
        active_touches = 'Active Touches: %d'%(self.number_of_active_touch)
        events = 'Events: '+','.join(self.event_list)
        return '\n'.join([slot_text,active_touches,events]) 
    
    #EVENT Handling functions
    def check_and_queue_event(self,event):
        if event is not None:
            self.output_event_queue.put_nowait(event)
    
    def abs_mt_slot(self,event):
        self.slot_for_next_report = event.value
        #print(event)
        pass

    def abs_mt_touch_major(self,event):
        self.slots[self.slot_for_next_report].touch_major = event.value        

    def abs_mt_touch_minor(self,event):
        self.slots[self.slot_for_next_report].touch_minor = event.value

    def abs_mt_width_major(self,event):
        self.slots[self.slot_for_next_report].width_major = event.value
        
    def abs_mt_width_minor(self,event):
        self.slots[self.slot_for_next_report].width_minor = event.value

    def abs_mt_orientation(self,event):
        self.slots[self.slot_for_next_report].orientation = event.value
        
    def abs_mt_position_x(self,event):
        self.slots[self.slot_for_next_report].abs_x = event.value 
        self.movement_flag = 1
        
    def abs_mt_position_y(self,event):
        self.slots[self.slot_for_next_report].abs_y = event.value
        self.movement_flag = 1
        
    def abs_mt_tool_type(self,event):
        pass

    def abs_mt_blob_id(self,event):
        pass
    
    def abs_mt_tracking_id(self,event):
        self.tracking_id_flag = 1
        if (event.value == -1):
            self.slots[self.slot_for_next_report].touch = 0
        else:
            self.slots[self.slot_for_next_report].touch = 1
            self.slots[self.slot_for_next_report].tracking_id = event.value

    def abs_mt_pressure(self,event):
        self.slots[self.slot_for_next_report].pressure = event.value
        #print(evdev.categorize(event))
        
    def abs_mt_distance(self,event):
        pass

    def abs_mt_tool_x(self,event):
        pass

    def abs_mt_tool_y(self,event):
        pass

    def syn_report(self,event):
        os.system('clear')
        
        self.timestamp = event.timestamp()
        self.update_internal_state_syn_report()

        print(self)

        if self.tracking_id_flag == 1:
            #This means that the number of fingers
            #on the touchpad has changed
            #Check on all events that depend on this kinda thing
            #Basically all events
            self.check_and_queue_event(check_for_tap_event(self))
            
        if self.movement_flag == 1:
            self.check_and_queue_event(check_single_tap_movement(self))
            
        self.save_last_state()
        print(self.__repr_tap_chain__())
            
        
    def btn_tool_quinttap(self,event):
        pass
    
    def btn_touch(self,event):
        pass
    
    def btn_tool_doubletap(self,event):
        pass
    
    def btn_tool_tripletap(self,event):
        pass
    
    def btn_tool_quadtap(self,event):
        pass

    def btn_tool_finger(self,event):
        pass

    #These are not really required as the ABS_MT_ABS_X versions
    #of these are still called
    def abs_x(self,event):
        #self.slots[0].abs_x = event.value
        #self.slots[0].touch = True
        #print(event.value)
        pass

    def abs_y(self,event):
        #self.slots[0].abs_y = event.value
        #self.slots[0].touch = True
        pass

    def abs_z(self,event):
        pass

    def abs_pressure(self,event):
        #self.slots[self.slot_for_next_report].pressure = event.value
        pass
    
    def abs_tool_width(self,event):
        pass

    
if __name__ == '__main__':
    async def touchpad_helper(event_queue):
        handler = MT_Handler(event_queue)
        touchpad = get_apple_touchpad()
        touchpad.grab()
        
        async for ev in touchpad.async_read_loop():
            #print(evdev.categorize(ev))
            #print(ev)
            handler.process_event(ev)
            #if ev.code == evdev.ecodes.ABS_MT_SLOT:
            #    print(evdev.categorize(ev))
            #    print(ev)
            #os.system('clear')

    async def tampabay(event_queue):
        sobj = SendUsbEvents()
        with open('evt_log','w') as evt_log: 
            evt_log.write("Opened Event Log at:%s\n"%datetime.datetime.now())
        while True:
            event = await event_queue.get()
            event(sobj)
            with open('evt_log','w') as evt_log: 
                evt_log.write("Event: %s\n"%event)


    #The following code is suitable for Python-3.7 asyncio
    async def main():
        event_queue = asyncio.Queue()
        mt_task = asyncio.create_task(touchpad_helper(event_queue))
        tpb_task = asyncio.create_task(tampabay(event_queue))
        await asyncio.gather(mt_task,tpb_task)
        
    asyncio.run(main())
    
    #The following code is suitable for Python-3.6 asyncio
    #loop = asyncio.get_event_loop()
    #event_queue = asyncio.Queue(loop = loop)
    #mt_task = loop.create_task(helper(touchpad))
    #tpb_task = loop.create_task(tampabay(event_queue))
    #loop.run_forever()

    #The following comes from the documentation of evdev
    #mt_task = asyncio.create_task(helper(touchpad))
    #asyncio.run_forever()
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(helper(touchpad))


    
