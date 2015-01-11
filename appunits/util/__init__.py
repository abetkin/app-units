import collections
import unittest

class NOT_SET:
    pass

class Case(unittest.TestCase):

    def runTest(self):
        pass

case = Case('runTest')

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


class DictAndList(list):
    '''
    A list backed by an ordered dict (formed from its values),
    providing element access by index as well as by key.

    Dict keys can not be ints.
    '''

    def __init__(self, *args, **kwargs):
        self._odict = collections.OrderedDict(*args, **kwargs)
        assert all(not isinstance(key, int) for key in self._odict), \
                "Dict keys can not be ints."
        super().__init__(self._odict.values())

    def key_index(self, key):
        if isinstance(key, int):
            return key
        return self.index(self[key])

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except TypeError:
            return self._odict[item]


class can_peek:

    def __init__(self, iterator):
        self._list = list(iterator)

    def peek(self):
        if not self._list:
            raise StopIteration()
        return self._list[0]

    def __iter__(self):
        while self._list:
            yield self._list.pop(0)
