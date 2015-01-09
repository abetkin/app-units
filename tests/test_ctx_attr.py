from appunits import ContextAttribute
from appunits.util import case

class A:

    def __init__(self):
        self.a = 1

    publish_attrs = ['a']

a_inst = A()

class B:
    def __init__(self):
        self.__pro__ = [a_inst]

    a = ContextAttribute('a')

b_inst = B()
case.assertEqual(b_inst.a, 1)

