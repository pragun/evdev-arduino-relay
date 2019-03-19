#This here takes care of 
# 1. listening to touchpad events
# 2. Updating touchpad state
# 3. Runinng gesture recognition 
# 4. And emitting sendMouse events

import evdev, asyncio, os
import datetime
from evdev_device_mappings import *
from sendusbevents import SendUsbEvents
from mouseoutputstack import MouseOutputStack
from collections import defaultdict
import csv

    
class MouseEventHandler(object):
    def __init__(self,sendUsbEvents):
        super().__init__()
        
        #The following variables hold state variables
        #for understanding sequential events
        self.sendUsbEvents = sendUsbEvents
        self.pressed_button = None
        self.rel_x_value = 0
        self.rel_y_value = 0
        self.rel_wheel_value = 0
        self.btn_mask_byte = 0
        self.btn_flag = 0
        self.rel_movement_flag = 0

        #This Flag is set when there is a change in the number of tracking ids
        
        self.handler_dict_abs = {
        }

        self.handler_dict_syn = {
            evdev.ecodes.SYN_REPORT : self.syn_report,
        }

        self.handler_dict_key = {
            evdev.ecodes.BTN_LEFT : self.btn_left,
            evdev.ecodes.BTN_RIGHT : self.btn_right,
            evdev.ecodes.BTN_MIDDLE : self.btn_middle,
            evdev.ecodes.BTN_EXTRA : self.btn_extra,
        }

        self.handler_dict_msc = defaultdict(lambda:self.do_nothing)
        

        self.handler_dict_rel = {
            evdev.ecodes.REL_X : self.rel_x,
            evdev.ecodes.REL_Y : self.rel_y,
            evdev.ecodes.REL_WHEEL : self.rel_wheel,
        }

        self.handler_dict = {
            evdev.ecodes.EV_SYN : self.handler_dict_syn,
            evdev.ecodes.EV_KEY : self.handler_dict_key,
            evdev.ecodes.EV_ABS : self.handler_dict_abs,
            evdev.ecodes.EV_REL : self.handler_dict_rel,
            evdev.ecodes.EV_MSC : self.handler_dict_msc,
        }

    def read_btn_config(self):
        expected_count = 6
        with open('btn_config','r',newline='') as f:
            reader = csv.reader((line for line in f if line[0]!= '#') ,delimiter='\t',skipinitialspace=True)
            output = []
            for row in reader:
                output.append([i.strip() for i in row if i != ''])
            output = [i for i in output if i != []]
            print(output)

    def cc_xy(self,cc_value_x,cc_value_y):
        def helperfunction(x,y):
            self.sendUsbEvents.midi_cc(cc_value_x,x)
            self.sendUsbEvents.midi_cc(cc_value_y,y)
        return helperfunction

    def cc_whl(self,cc_value):
        def helpferfunction(whl):
            self.sendUsbEvents.midi_cc(cc_value,whl)
        return helperfunction

    def report_movement(self,factor):
        def helperfunction(x,y):
                self.sendUsbEvents.move_mouse(int(x/factor),int(y/factor))            
        return helperfunction

    def report_scroll(self):
        def helperfunction(whl):
            self.sendUsbEvents.<Report scroll>
        return helperfunction
    
    
    def do_nothing(self,event):
        pass
    
    def process_mouse_event(self,event):
        try:
            self.handler_dict[event.type][event.code](event)
        except Exception as e:
            print("Exception:",e) 
            print("Event Categorize:",evdev.categorize(event))
            print(event)

    def process_keyboard_event(self,event):
        if (event.value):
            self.pressed_key = event.code
            
            print("Event Cat:",evdev.categorize(event))
            print(event)
            
    #This is the event that ties everything together
    #In other words, when this is received we
    # 1. Update the trackpad state with all the information we've received
    # 2. See if that requires us to send out any mouse events
    # 3. Prepare for receiving the next SYN event, whenever that will happen

    def rel_x(self,event):
        self.rel_x_value = event.value
        self.rel_movement_flag = True

    def rel_y(self,event):
        self.rel_y_value = event.value
        self.rel_movement_flag = True

    def rel_wheel(self,event):
        self.rel_wheel_value = event.value
        self.rel_wheel_flag = True

    def btn_left(self,event):
        self.btn_flag = True
        self.btn_left_value = event.value
        if(event.value):
            self.btn_mask_byte |= 0x1
        else:
            self.btn_mask_byte &= 0b11111110
        
    def btn_right(self,event):
        self.btn_flag = True
        self.btn_right_value = event.value
        if(event.value):
            self.btn_mask_byte |= 0x2
        else:
            self.btn_mask_byte &= 0b11111101

    def btn_middle(self,event):
        self.btn_flag = True
        self.btn_middle_value = event.value
        if(event.value):
            self.btn_mask_byte |= 0x4
        else:
            self.btn_mask_byte &= 0b11111011

    def btn_extra(self,event):
        print("btn extra",event.value)
        
    def syn_report(self,event):
        if self.btn_flag:
            self.sendUsbEvents.button_state((self.btn_mask_byte|0b10000000))
            self.btn_flag = False
            
        if self.pressed_button == None:
            if self.rel_x_value != 0 or self.rel_y_value != 0:
                self.sendUsbEvents.move_mouse(int(self.rel_x_value/fast_factor),int(self.rel_y_value/fast_factor))
            if self.rel_wheel_value != 0:
                self.sendUsbEvents.scroll_mouse(self.rel_wheel_value,0)
               
        self.rel_x_value = 0
        self.rel_y_value = 0
        self.rel_wheel_value = 0

if __name__ == '__main__':
    sendUsbEvents = SendUsbEvents(dummy=False)
    utech_mouse_event_handler = MouseEventHandler(sendUsbEvents)

    mouse = evdev.InputDevice(utech_mouse)
    keyboard = evdev.InputDevice(utech_keyboard)

    mouse.grab()
    keyboard.grab()

    async def mouse_event_loop():
        async for ev in mouse.async_read_loop():
            utech_mouse_event_handler.process_mouse_event(ev)

    async def keyboard_event_loop():
        async for ev in keyboard.async_read_loop():
            utech_mouse_event_handler.process_keyboard_event(ev)
        
    async def main():
        mouse_event_handler_task = asyncio.create_task(mouse_event_loop())
        keyboard_event_handler_task = asyncio.create_task(keyboard_event_loop())
        await asyncio.gather(mouse_event_handler_task, keyboard_event_handler_task)
        
    asyncio.run(main())
