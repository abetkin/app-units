from functools import partial
from collections import OrderedDict


from .util.mro import _mro
from .util.deps import sort_by_deps, breadth_first, depth_first

from .marks import CollectMarksMeta

class UnitConfigError(Exception):
    pass


# TODO states: prepared, app1, app2, ...
# TODO ability to specify order manually!!
# incapsulation!
# option: ignore warnings

class AppUnit(metaclass=CollectMarksMeta):
    '''
    '''
    depends_on = ()
    parents = None # FIXME ordered, deps -> depends_on

    def __init__(self, identity=None, depends_on=None, parents=None):
        if identity is not None:
            self.identity = identity
        else:
            self.identity = self.__class__
        if depends_on is not None:
            self.depends_on = depends_on
        if parents is not None:
            self.parents = parents
        if self.parents is None:
            if isinstance(self.deps, set):
                raise UnitConfigError("Unit parents are not specified. Can't "
                                      "use dependencies because it's a set.")
            self.parents = list(self.deps)
        self.state = '-'

    # def _instantiate_deps(self):
    #     '''
    #     '''
    #     deps = tuple(self.deps.pop() for i in range(len(self.deps)))
    #     for dep in deps:
    #         if isinstance(dep, type) and issubclass(dep, AppUnit):
    #             dep = dep()
    #             # ! dep.prepare()
    #         dep.parents.update(self.propagated_parents)
    #         self.deps.add(dep)
    #         yield dep
            # TODO is not exhausted

    def _make_deps(unit):
        container = type(unit.depends_on) # todo forbid iterator

        def generate():
            for dep in unit.depends_on:
                if isinstance(dep, type) and issubclass(dep, AppUnit):
                    dep = dep()
                yield dep

        self.depends_on = container(generate())
        yield from self.depends_on
        # for dep in self.depends_on:
        #     dep.Prepare(unit)
        #     yield dep

    '''
    @property
    def depends_on(self):
    '''

    def Prepare(self, master_unit):
        shared_parents = (p for p in master_unit.parents
                          if p.share_context)
        self.parents.extend(shared_parents)

    def prepare(self):
        # TODO comments
        all_deps = breadth_first(self, AppUnit._make_deps)
        next(all_deps)
        all_deps = {dep.identity: dep for dep in all_deps}

        deps_dict = {dep.identity: tuple(d.identity for d in dep.deps)
                     for dep in all_deps.values()}

        def units():
            for units in sort_by_deps(deps_dict):
                for name in units:
                    yield all_deps[name]
            yield self

        def children(unit):
            for dep in

        units_order = list(depth_first(self))

        def units(self):
            for units in sort_by_deps(deps_dict):
                while self.depends_on[0] in units:
                    yield self.depends_on.pop(0)

        units = list(units())




        for unit in get_units_order(self):
            # TODO prepare deps:
            # dep.Prepare(unit)
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
        return iter(self.deps)


    def run(self):
        # if order is not defined manually:
        if self.state == '-':
            self.prepare()
        for dep in self:
            dep.result = dep.main()
        #/ else ...
        self.result = self.main()
        return self.result

    # TODO!! detect cycles & invalid config

# TODO test!: units same deps

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
