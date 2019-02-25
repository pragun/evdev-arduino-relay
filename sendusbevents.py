import serial

class SendUsbEvents(object):
    def __init__(self,port='/dev/ttyACM0',speed=1000000,dummy=True):
        #Update this list as more functions are added
        self.handler_list = [ \
                              'send_as_mouse', \
                              'tap_click', \
                              'move_mouse', \
                              'scroll_mouse', \
                              'three_mouse', \
                              'four_mouse', \
                              'five_mouse', \
                              'press_button',\
                              'release_button']
        if dummy:
            self.ser = open('serial.dummy','wb')
        else:
            self.ser = serial.Serial(port,speed)

        self.handler_dict = {}
        self.create_handler_dict()

    def create_handler_dict(self):
        for i in self.handler_list:
            self.handler_dict[i] = getattr(self,i)

    def do(self,call_name,*args):
        print(self.handler_dict)
        print(call_name)
        self.handler_dict[call_name](*args)
            
    def send_as_mouse(self,arr):
        arr2 = [ord('a')]+arr+[ord('\n')]
        print(bytes(arr2))
        self.ser.write(bytes(arr2))
        
    def tap_click(self,num):
        tap_byte = 0b00000001 << (num-1)
        tap_byte |= 0b10000000
        arr = [tap_byte,0,0,0,0]
        self.send_as_mouse(arr)
        
    def move_mouse(self,x,y):
        if x<0:
            x=256-abs(x)
        if y<0:
            y=256-abs(y)
        arr = [0,x,y,0,0]
        self.send_as_mouse(arr)
        
    def scroll_mouse(self,x,y):
        if x<0:
            x=256-abs(x)
        if y<0:
            y=256-abs(y)
        arr = [0,0,0,x,y]
        self.send_as_mouse(arr)

    def three_mouse(self):
        pass

    def four_mouse(self):
        pass

    def five_mouse(self):
        pass

    def press_button(self,num):
        pass

    def release_button(self,num):
        pass
    
    def disconnect(self):
        self.ser.close()

        
if __name__ == '__main__':
    a = SendUsbEvents()
    a.tap_click(3)
    a.move(100,100)
    a.disconnect()
        
