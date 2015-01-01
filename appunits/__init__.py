from .util.mro import _mro
from .util.deps import sort_by_deps, breadth_first

from functools import partial

class AppUnit(object):
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
            self.deps = deps
        if parents is not None:
            self.parents = parents
        if self.parents is None:
            self.parents = self.deps

    @property
    def propagated_parents(self):
        return [parent for parent in self.parents
                if getattr(parent, 'propagate', False)]

    def create_deps(self):
        for dep in self.deps:
            if isinstance(dep, type):
                dep = dep()
            dep.parents.update(self.propagated_parents)
            yield dep

    def traverse_deps(self):
        '''breadth-first
        '''
        deps_dict = {}

        def log(unit, dep):
            if unit == self:
                return
            deps_dict.setdefault(unit.identity, set()).add(dep.identity)

        deps = breadth_first(self, AppUnit.create_deps, log=log)
        # TODO if cycles, raise exc
        next(deps)
        return (set(deps), # FIXME: take first
                deps_dict)

    def get_pro(self):
        return _mro(self.parents,
                    lambda obj: getattr(obj, '__pro__', ()))

    def main(self):
        '''
        You should implement this.
        '''

    def __repr__(self):
        return 'Unit %s' % repr(self.identity)

    def __hash__(self):
        return hash(self.identity)

    def __eq__(self, other):
        if isinstance(other, AppUnit):
            return self.identity == other.identity

    def run(self):
        self.all_deps, deps_dict = self.traverse_deps()
        for dep in self.all_deps:
            deps_dict.setdefault(dep.identity, set())
        def ordered_units():
            for units in sort_by_deps(deps_dict):
                yield from units

        all_deps = dict(((u.identity, u) for u in self.all_deps))
        for dep_name in ordered_units():
            dep = all_deps[dep_name]
            dep.run()
        self.__pro__ = self.get_pro()
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
