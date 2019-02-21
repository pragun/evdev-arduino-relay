import serial

class SendUsbEvents(object):
    def __init__(self,port='/dev/ttyACM0',speed=1000000):
        self.ser = serial.Serial(port,speed)

    def send_as_mouse(self,arr):
        arr2 = [ord('a')]+arr+[ord('\n')]
        print(bytes(arr2))
        self.ser.write(bytes(arr2))

    def tap_click(self,num):
        tap_byte = 0b00000001 << (num-1)
        tap_byte |= 0b10000000
        arr = [tap_byte,0,0,0,0]
        self.send_as_mouse(arr)

    @staticmethod
    def tap_click_queue_object(num):
        def a(sobj):
            return sobj.tap_click(num)
        return a

    @staticmethod
    def move_mouse_queue_object(x,y):
        if x<0:
            x=256-abs(x)
        if y<0:
            y=256-abs(y)
            
        def a(sobj):
            return sobj.move_mouse(x,y)
        return a

    def move_mouse(self,x,y):
        arr = [0,x,y,0,0]
        self.send_as_mouse(arr)
        
    def disconnect(self):
        self.ser.close()

        
if __name__ == '__main__':
    a = SendUsbEvents()
    a.tap_click(3)
    a.move(100,100)
    a.disconnect()
        
