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
key_config_filename = 'key_config'
from tabulate import tabulate
import math
import arduino_keys

wait_num_reports = 2

sign = lambda x: (1, -1)[x<0]

class MouseEventHandler(object):
    def __init__(self,sendUsbEvents):
        super().__init__()
        
        #The following variables hold state variables
        #for understanding sequential events
        self.sendUsbEvents = sendUsbEvents
        self.rel_x_value = 0
        self.rel_y_value = 0
        self.rel_wheel_value = 0
        self.btn_mask_byte = 0
        self.btn_flag = 0
        self.rel_movement_flag = 0
        self.rel_wheel_flag = 0
        
        self.pressed_key = None
        self.last_pressed_key = None

        #This little guy can be used by a movement reporting function
        #such as 'std_cc_xy' to save a tuple
        #containing the integrated distance travelled since the last click
        #or the initial position of the X,Y click
        self.movement_last_reported_state = None
        
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

        self.key_dict_movement = {}
        self.key_dict_press_release = {}
        self.key_dict_wheel = {}

        self.read_key_config()

    def read_key_config(self):
        key_config_token_list = None
        with open(key_config_filename,'r',newline='') as f:
            output = []
            for line in f:
                if line.startswith('#'):
                    continue #Ignore comments, like this one here :)
                output.append(line.split())
            output = [i for i in output if i != []]
            print(tabulate(output))
            key_config_token_list = output

        for line in key_config_token_list:
            print(line)
            [key_dict_key,movement_handler,wheel_handler,press_release_handler] = line
            key_dict_key = eval(key_dict_key)
            self.key_dict_movement[key_dict_key] = eval('self.'+movement_handler)
            self.key_dict_wheel[key_dict_key] = eval('self.'+wheel_handler)
            self.key_dict_press_release[key_dict_key] = eval('self.'+press_release_handler)

        print("Loaded Key Configuration Successfully.")

#All of these here, till #end_of_config functions
#can be used in the key_config file to denote
#what should happen if the keys are pressed and released
#and if the mouse is moved when the keys are pressed
    def note_on_off(self,note):
        def helperfunction(key_up_down_value):
            if key_up_down_value == 1:
                self.sendUsbEvents.midi_note_on(note,127)
            if key_up_down_value == 0:
                self.sendUsbEvents.midi_note_off(note,127)
        return helperfunction                
    
    def std_cc_xy(self):
        def helperfunction(x,y,last_state):
            if last_state == None:
                return wait_num_reports #wait_num_reports
            if type(last_state) == int and last_state > 0:
                return last_state - 1            
            #This scheme up here helps us ignore
            #'wait_num_reports' number of movement reports
            #right after a key-press as kind of a simple
            #movement_debouncing_mechanism
            
            if type(last_state) == int and last_state == 0:
                last_state = (0,0) #[Integrated distance, total delX, delY since beginning of gesture]

            x = min(x,63) if x>0 else max(x,-63)
            y = min(y,63) if y>0 else max(y,-63)
            self.sendUsbEvents.midi_cc(1,x)
            self.sendUsbEvents.midi_cc(2,y)
            (rx,ry) = last_state
            new_rx = rx+x
            new_ry = ry+y
            del_r = int(math.sqrt(new_rx**2+new_ry**2)-math.sqrt(rx**2+ry**2))
            self.sendUsbEvents.midi_cc(3,del_r)
            del_d = int(math.sqrt(x**2+y**2))
            self.sendUsbEvents.midi_cc(4,del_d)
            return (new_rx,new_ry)
        return helperfunction

    
    def report_xy_as_scroll(self,divisor):
        def helperfunction(x,y,last_state):
            #print('X:%d,Y:%d'%(x,y,))
            if last_state == None:
                return wait_num_reports
            if type(last_state) == int and last_state > 0:
                return last_state - 1            
            #This scheme up here helps us ignore
            #'wait_num_reports' number of movement reports
            #right after a key-press as kind of a simple
            #movement_debouncing_mechanism
            
            if type(last_state) == int and last_state == 0:
                last_state = (0,0) #[Integrated distance, total delX, delY since beginning of gesture]

            (x_remainder,y_remainder) = last_state
            x_total = x+x_remainder
            y_total = y+y_remainder
            x_remainder = (x_total)%divisor
            y_remainder = (y_total)%divisor
            self.sendUsbEvents.scroll_mouse(int(y_total/divisor),int(x_total/divisor))
            return (x_remainder,y_remainder)
        
        return helperfunction

    def report_xy_as_cursor(self,divisor):
        def helperfunction(x,y,last_state):
            if last_state == None:
                return wait_num_reports
            if type(last_state) == int and last_state > 0:
                return last_state - 1            
            #This scheme up here helps us ignore
            #'wait_num_reports' number of movement reports
            #right after a key-press as kind of a simple
            #movement_debouncing_mechanism
            
            if type(last_state) == int and last_state == 0:
                last_state = (0,0) #[Integrated distance, total delX, delY since beginning of gesture]

            (x_remainder,y_remainder) = last_state
            x_total = x+x_remainder
            y_total = y+y_remainder

            #print('X:%d, Y:%d, Xt:%d,Yt:%d, Xr:%d, Yr:%d'%(x,y,x_total,y_total,x_remainder,y_remainder))
            
            x_remainder = sign(x_total)*(abs(x_total)%divisor)
            y_remainder = sign(y_total)*(abs(y_total)%divisor)
            x_quot = int(x_total/divisor)
            y_quot = int(y_total/divisor)

            if x_quot >= 1:
                self.sendUsbEvents.keyboard_press(arduino_keys.KEY_RIGHT_ARROW)
                self.sendUsbEvents.keyboard_release(arduino_keys.KEY_RIGHT_ARROW)
                return (x_remainder,0)
            
            if x_quot <= -1:
                self.sendUsbEvents.keyboard_press(arduino_keys.KEY_LEFT_ARROW)
                self.sendUsbEvents.keyboard_release(arduino_keys.KEY_LEFT_ARROW)
                return (x_remainder,0)
            
            if y_quot >= 1:
                self.sendUsbEvents.keyboard_press(arduino_keys.KEY_DOWN_ARROW)
                self.sendUsbEvents.keyboard_release(arduino_keys.KEY_DOWN_ARROW)
                return (0,y_remainder)
            
            if y_quot <= -1:
                self.sendUsbEvents.keyboard_press(arduino_keys.KEY_UP_ARROW)
                self.sendUsbEvents.keyboard_release(arduino_keys.KEY_UP_ARROW)
                return (0,y_remainder)

            return (x_remainder,y_remainder)

            #print('X:%d,Y:%d,R:%f'%(x,y,x/float(y)))
        return helperfunction

    def key_press_release(self,key_code,no_movement=True):
        def helperfunction(key_up_down_value):
            pass
        return helperfunction
    
    def cc_whl(self,cc_value):
        def helperfunction(whl):
            self.sendUsbEvents.midi_cc(cc_value,whl)
        return helperfunction

    def report_movement(self,factor):
        def helperfunction(x,y,last_state):
            #print('RM x:%d, y:%d'%(x,y))
            self.sendUsbEvents.move_mouse(int(x/factor),int(y/factor))            
        return helperfunction

    def report_scroll(self):
        def helperfunction(whl):
            self.sendUsbEvents.scroll_mouse(whl,0)
        return helperfunction
    
    def do_nothing(self,*args): #Wu-Wei
        def helperfunction():
            pass
        return helperfunction
#end_of_key_config_functions

    def process_mouse_event(self,event):
        try:
            self.handler_dict[event.type][event.code](event)
        except Exception as e:
            print("Exception:",e) 
            print("Event Categorize:",evdev.categorize(event))
            print(event)

    def process_keyboard_event(self,event):
        if event.type == 1:
            #print("Event Cat:",evdev.categorize(event))
            #print(event)
            if event.value == 1: #Key Down
                self.pressed_key = event.code
                self.movement_last_reported_state = None #This is reset for every new click
                self.key_dict_press_release[self.pressed_key](event.value)
                
            if event.value == 0: #Key Up
                self.last_pressed_key = self.pressed_key
                self.pressed_key = None
                self.key_dict_press_release[self.last_pressed_key](event.value)                    
                
            
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

        if self.rel_movement_flag:
            self.movement_last_reported_state = self.key_dict_movement[self.pressed_key]\
                (self.rel_x_value,self.rel_y_value,self.movement_last_reported_state)
            self.rel_movement_flag = False
            
        if self.rel_wheel_flag:
            self.key_dict_wheel[self.pressed_key](self.rel_wheel_value)
            self.rel_wheel_flag = False

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
