from copy import copy
from collections import OrderedDict
from abc import ABCMeta

from .util import common_superclass

class Mark(metaclass=ABCMeta):

    COLLECT_INTO = '_marks'

    def __init__(self, **kwargs):
        self.source_function = None
        self.__dict__.update(kwargs)

    def __call__(self, f):
        self.source_function = f
        return self

    def build(self, klass):
        '''
        Construct an instance from Mark. You should override this.
        '''
        return self

    @classmethod
    def build_all(cls, marks_dict, klass):
        for key, m in marks_dict.items():
            marks_dict[key] = m.build(klass)
        return marks_dict

    @classmethod
    def _add_all(cls, marks_dict, klass):
        if not marks_dict:
            return
        supercls = common_superclass(marks_dict.values())
        built_dict = supercls.build_all(marks_dict, klass)
        setattr(klass, supercls.COLLECT_INTO, built_dict)


class CollectMarksMeta(type):
    '''
    The metaclass collects `Mark` instances from the classdict
    and then removes from the class namespace.
    '''

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return OrderedDict()

    def __new__(cls, name, bases, namespace):
        marks_dict = OrderedDict()
        for key, obj in namespace.items():
            if not isinstance(obj, Mark):
                continue
            # make clones if necessary so that all marks
            # were different objects
            if obj in marks_dict.values():
                obj = copy(obj)
            marks_dict[key] = obj

        # clear the namespace
        for name in marks_dict:
            del namespace[name]

        klass = type.__new__(cls, name, bases, namespace)
        Mark._add_all(marks_dict, klass)
        return klass
