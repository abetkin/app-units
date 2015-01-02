from copy import copy
from collections import OrderedDict
from abc import ABCMeta

class mark(metaclass=ABCMeta):

    def __init__(self, **kwargs):
        self.source_function = None
        self.__dict__.update(kwargs)

    def __call__(self, f):
        self.source_function = f
        return self

    def build(self, owner):
        '''
        Construct an instance from mark. You should override this.
        '''
        return self


class CollectMarksMeta(type):
    '''
    A metaclass that collects `mark` instances from the classdict
    and puts them in `_marks` attribute, so that their names
    won't collide with regular methods' names.
    '''

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return OrderedDict()

    def __new__(cls, name, bases, namespace):
        import ipdb; ipdb.set_trace()  # breakpoint d7085a11 //

        marks_dict = OrderedDict()
        for key, obj in namespace.items():
            if not isinstance(obj, mark):
                continue
            # make clones if necessary so that all marks
            # were different objects
            if obj in marks_dict.values():
                obj = copy(obj)
            marks_dict[key] = obj

        # clear the namespace
        for name in marks_dict:
            del namespace[name]

        namespace['_marks'] = marks_dict
        klass = type.__new__(cls, name, bases, namespace)
        for name, m in marks_dict.items():
            marks_dict[key] = m.build(klass)
        return klass