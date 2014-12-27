from .util.mro import _mro
from .util.deps import sort_by_deps

class UnitsRunner(object):

    def __init__(self, units):
        self.units = units

    # TODO identity policy

    def get_units_order(self):

        def add_units(units, result):
            for unit in units:
                if unit in result:
                    # TODO forbid units with the same identity'
                    continue
                result[unit] = unit.deps
                add_units(unit.deps, result)

        deps_dict = {}
        add_units(self.units, deps_dict)

        def units_ordered():
            for units in sort_by_deps(deps_dict):
                yield from units

        return list(units_ordered())
                    

class ClassIdentity(object):

    def __init__(self, cls):
        self.cls = cls

    def __str__(self):
        return self.cls.__name__

    __repr__ = __str__



class AppUnit(object):

    # deps = ()
    # identity = None

    def __init__(self, deps=(), identity=None):
        # Init the config. Optional
        #
        self.deps = deps
        self.identity = identity

    # FIXME view is always the context

    def get_identity(self):
        return self.identity if self.identity is not None \
                else ClassIdentity(self.__class__)

    def __hash__(self):
        return hash(self.get_identity())

    def _get_parents(self):
        return self.deps # TODO not always

    @staticmethod
    def _get_pro(obj):
        return getattr(obj, '__pro__', ())

    def run(self):
        self.__pro__ = _mro(self._get_parents(), get_mro=self._get_pro())
        return self()

    def __repr__(self):
        return repr(self.get_identity())


class ContextAttribute:
    '''
    An attribute that is looked up in the (parent) context.

    "__pro__" stays for "parent resolution order".
    '''

    PUBLISHED_CONTEXT_ATTR = 'published_context'
    PUBLISHED_CONTEXT_EXTRA_ATTR = 'published_context_extra'

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance:
            return self._lookup(instance)
        return self

    def _lookup(self, instance):
        for obj in instance.__pro__:
            published_context = getattr(obj, self.PUBLISHED_CONTEXT_ATTR, ())
            if self.name in published_context:
               return getattr(obj, self.name)
            published_context_extra = getattr(obj,
                    self.PUBLISHED_CONTEXT_EXTRA_ATTR, ()) # normally a dict
            if self.name in published_context_extra:
               return obj.published_context_extra[self.name]
        raise AttributeError(self.name)
