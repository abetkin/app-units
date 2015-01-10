import collections
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

# copied almost entirely from rest_framework.fields.get_attribute
def get_attribute(instance, attrs):
    """
    Similar to Python's built in `getattr(instance, attr)`,
    but takes a list of nested attributes, instead of a single attribute.

    Also accepts either attribute lookup on objects or dictionary lookups.
    """
    for attr in attrs:
        if instance is None:
            # Break out early if we get `None` at any point in a nested lookup.
            return None
        if isinstance(instance, collections.Mapping):
            instance = instance[attr]
        else:
            instance = getattr(instance, attr)
    return instance