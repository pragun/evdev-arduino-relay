class P(object):
    def __init__(self,a):
        self.a = a
        self.handlerdict = {'b':self.b,
                            'c':self.c}
        

    def b(self):
        print("b")

    def c(self):
        print("c")

    def handle(self,inp):
        self.handlerdict[inp]()
        
