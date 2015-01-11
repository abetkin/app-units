from copy import copy
from collections import OrderedDict
from abc import ABCMeta
from functools import partial

from .util import common_superclass

class Mark(metaclass=ABCMeta):

    collect_into = '_marks'

    def __init__(self, **kwargs):
        self.source_function = None
        self.__dict__.update(kwargs)

    def __call__(self, f):
        self.source_function = f
        return self

    def build_mark(self, klass):
        '''
        Construct an instance from Mark. You should override this.
        '''
        return self

    @classmethod
    def _add_all(cls, marks_dict, klass):
        for key, mark in marks_dict.items():
            try:
                built_mark = mark.build_mark(klass)
            except AttributeError:
                built_mark = mark
            collect_into = getattr(mark, 'collect_into', Mark.collect_into)
            if not collect_into in klass.__dict__:
                setattr(klass, collect_into, OrderedDict([(key, built_mark)]))
            else:
                getattr(klass, collect_into)[key] = built_mark


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
        for _name in marks_dict:
            del namespace[_name]

        klass = type.__new__(cls, name, bases, namespace)
        Mark._add_all(marks_dict, klass)
        return klass
