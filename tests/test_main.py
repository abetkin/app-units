from appunits import ContextAttribute

class A:

    def __init__(self):
        self.a = 1
        
    published_context = ['a']

a_inst = A()

class B:
    def __init__(self):
        self.__pro__ = [a_inst]
    
    a = ContextAttribute('a')

b_inst = B()
assert b_inst.a == 1

