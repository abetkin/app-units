from functools import partial
from collections import OrderedDict


from .util.mro import _mro
from .util.deps import sort_by_deps, breadth_first

from .marks import CollectMarksMeta

# TODO states: prepared, app1, app2, ...

class AppUnit(metaclass=CollectMarksMeta):
    '''
    '''
    deps = set()
    parents = None

    def __init__(self, identity=None, deps=None, parents=None):
        if identity is not None:
            self.identity = identity
        else:
            self.identity = self.__class__
        if deps is not None:
            self.deps = set(deps)
        if parents is not None:
            self.parents = set(parents)
        if self.parents is None:
            self.parents = set(self.deps)
        self.state = '-'

    @property
    def propagated_parents(self):
        return [parent for parent in self.parents
                if getattr(parent, 'propagate', False)]

    def _instantiate_deps(self):
        '''
        '''
        deps = tuple(self.deps.pop() for i in range(len(self.deps)))
        for dep in deps:
            if isinstance(dep, type) and issubclass(dep, AppUnit):
                dep = dep()
            dep.parents.update(self.propagated_parents)
            self.deps.add(dep)
            yield dep
            # TODO is not exhausted


    def prepare(self):
        # TODO comments
        all_deps = breadth_first(self, AppUnit._instantiate_deps)
        next(all_deps)
        all_deps = {dep.identity: dep for dep in all_deps}

        deps_dict = {dep.identity: tuple(d.identity for d in dep.deps)
                     for dep in all_deps.values()}

        def units():
            for units in sort_by_deps(deps_dict):
                for name in units:
                    yield all_deps[name]
            yield self

        units = list(units())

        for unit in units:
            assert all(dep.state == 'prepared' for dep in unit.deps)
            deps_of_deps = {d.identity for dep in unit.deps for d in dep.deps}
            unit.deps = deps_of_deps | {dep.identity for dep in unit.deps}
            unit.deps = (all_deps[name] for name in unit.deps)
            unit.deps = sorted(unit.deps, key=units.index)
            unit.deps = OrderedDict((d.identity, d) for d in unit.deps)
            unit.__pro__ = unit.get_pro()
            unit.state = 'prepared'

    def get_pro(self):
        return _mro(self.parents,
                    lambda obj: getattr(obj, '__pro__', ()))

    def main(self):
        '''
        You should implement this.
        '''

    def __repr__(self):
        return 'Unit %s' % repr(self.identity)

    __str__ = __repr__

    def __hash__(self):
        return hash(self.identity)

    def __eq__(self, other):
        if isinstance(other, AppUnit):
            return self.identity == other.identity

    # Recursion should happen only when traversing
    #

    def __iter__(self):
        assert self.state == 'prepared'
        return iter(self.deps.values())


    def run(self):
        if self.state == '-':
            self.prepare()
        for dep in self:
            dep.result = dep.main()
        self.result = self.main()
        return self.result

    # TODO!! detect cycles & invalid config


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
