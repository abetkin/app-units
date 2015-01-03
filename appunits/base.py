from functools import partial
from collections import OrderedDict


from .util.mro import _mro
from .util.deps import sort_by_deps, breadth_first

from .marks import CollectMarksMeta

class AppUnit(metaclass=CollectMarksMeta):
    '''
    '''
    # states: prepared, app1, app2, ...
    depends_on = set()
    parents = None

    def __init__(self, identity=None, depends_on=None, parents=None):
        if identity is not None:
            self.identity = identity
        else:
            self.identity = self.__class__
        if depends_on is not None:
            self.depends_on = set(depends_on)
        if parents is not None:
            self.parents = set(parents)
        if self.parents is None:
            self.parents = set(self.depends_on)
        self.state = '-'
        self.deps = set()

    @property
    def propagated_parents(self):
        return [parent for parent in self.parents
                if getattr(parent, 'propagate', False)]

    def _create_dep(self, dep):
        if isinstance(dep, type) and issubclass(dep, AppUnit):
            dep = dep()
        dep.parents.update(self.propagated_parents)
        return dep

    def _iter_deps(self):
        # the iterator of node's children
        # (is used for traversing the dependency tree)

        # TODO: replace
        for dep in self.depends_on.pop():
            dep = self.create_dep(dep)
            if dep not in self.deps:
                self.deps.add(dep)
            yield dep

    def prepare(self):
        1
        # assert all deps prepared


    # prepare <-> pro

    def prepare_all(self):
        list(breadth_first(self, AppUnit._iter_deps))

        deps_dict = {dep: dep.deps for dep in self.deps}

        def units():
            for units in sort_by_deps(deps_dict):
                yield from units
            yield self

        for unit in units:
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

    def prepare_(self, # deps=None, deps_dict=None
            ):
        all_deps, deps_dict = self.traverse_deps()
        self.deps = OrderedDict((dep.identity, dep) for dep in all_deps)
        for dep in all_deps:
            deps_dict.setdefault(dep.identity, set())

        # just the top app needs this
        self._deps_order = []
        for units in sort_by_deps(deps_dict):
            self._deps_order.extend(units)

        for dep_name in self._deps_order:
            dep = self.deps[dep_name]
            dep.prepare()
        self.__pro__ = self.get_pro()
        self.prepared = True

    def __iter__(self):
        try:
            deps_order = self._deps_order
        except AttributeError as e:
            raise AppUnitError('%s is not prepared' % self) from e
        for dep_name in deps_order:
            yield self.deps[dep_name]

    def run(self):
        if not self.prepared:
            self.prepare()
        for dep in self:
            dep.main()
        self.result = self.main()
        return self.result

    # TODO!! detect cycles & invalid config

class AppUnitError(Exception):
    pass


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
