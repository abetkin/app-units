
import unittest

class NOT_SET:
    pass

class Case(unittest.TestCase):

    def runTest(self):
        pass

case = Case('runTest')

def common_superclass(objects):
    supercls = None
    for obj in objects:
        if not supercls:
            supercls = type(obj)
            continue
        while not isinstance(obj, supercls):
            supercls = supercls.__mro__[1]
    return supercls
