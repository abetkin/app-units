from .util.mro import _mro
from .util.deps import sort_by_deps


class ClassIdentity(object):

    def __init__(self, cls):
        self.cls = cls

    def __str__(self):
        return self.cls.__name__

    def __hash__(self):
        return hash(self.cls)

    __repr__ = __str__


class AppUnit(object):
    '''
    Is instantiated at the "prepare" stage.
    '''

    def __init__(self, identity=None, deps=()):
        if identity is not None:
            self.identity = identity
        else:
            self.identity = ClassIdentity(self.__class__)
        self.deps = deps

    # TODO be able exclude context from some apps

    @classmethod
    def reorder(cls, units):
        all_units = {}

        def get_deps(unit, result=None):
            all_units.setdefault(unit.identity, unit)
            if result is None:
                result = []
            for unit in unit.deps:
                if unit in result:
                    # TODO forbid units with the same identity
                    continue
                result.append(unit.identity)
                result.extend(get_deps(unit, result))
            return result

        deps_dict = {u.identity: get_deps(u) for u in units}

        def units_order():
            for units in sort_by_deps(deps_dict):
                yield from units

        return [all_units[id] for id in units_order()]

    @staticmethod
    def _get_pro(obj):
        return getattr(obj, '__pro__', ())

    # def run(self):
    #     self.__pro__ = _mro(self._get_parents(), get_mro=self._get_pro())
    #     return self()

    def __repr__(self):
        return repr(self.identity)

    def _run(self):
        'Assume all the dependencies satisfied'



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
