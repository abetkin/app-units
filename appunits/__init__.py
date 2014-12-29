from .util.mro import _mro
from .util.deps import sort_by_deps


class ClassIdentity(object):

    def __init__(self, cls):
        self.cls = cls

    def __str__(self):
        return self.cls.__name__

    def __hash__(self):
        return hash(self.cls)

    def __eq__(self, other):
        if isinstance(other, ClassIdentity):
            return self.cls == other.cls
        return self.cls == other

    __repr__ = __str__


def instantiate(units):
    return [unit() if isinstance(unit, type) else unit
            for unit in units]


class UnitsRunner(object):

    def __init__(self, units):
        self.units = instantiate(units)

    def prepare(self):
        deps_dict = {u: u.get_deps() for u in self.units}

        def ordered_units():
            for units in sort_by_deps(deps_dict):
                yield from units

        return list(ordered_units())




    def run(self):
        self.all_units = self.prepare()
        # TODO error handling
        for unit in self.all_units:
            try:
                unit.run()
            finally:
                print("App: %s" % unit.identity)


class AppUnit(object):
    '''
    '''

    def __init__(self, identity=None, deps=(),
                 parents=None):
        if identity is not None:
            self.identity = identity
        else:
            self.identity = ClassIdentity(self.__class__)
        self.deps = instantiate(deps)
        if parents is None:
            self.parents = self.deps
        else:
            self.parents = instantiate(parents)

    def get_deps(self, result=None):
        if result is None:
            result = []
        for unit in self.deps:
            if unit in result:
                # TODO forbid units with the same identity
                continue
            result.append(unit)
            result.extend(unit.get_deps(result))
        return result

    # TODO be able exclude context from some apps

    def get_pro(self):
        return _mro(self.parents,
                    lambda obj: getattr(obj, '__pro__', ()))

    def __hash__(self):
        return hash(self.identity)

    def __eq__(self, other):
        if isinstance(other, AppUnit):
            return self.identity == other.identity
        return self.identity == other

    def run(self):
        raise NotImplementedError()

    def __repr__(self):
        return repr(self.identity)

    def __call__(self):
        self.__pro__ = self.get_pro()
        self.result = self.run()
        return self.result



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
