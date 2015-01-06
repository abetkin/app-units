import inspect
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

#

class AppUnit(metaclass=CollectMarksMeta):
    '''
    '''
    depends_on = ()
    parents = None

    def __init__(self, identity=None, depends_on=None, parents=None):
        if identity is not None:
            self.identity = identity
        else:
            self.identity = self.__class__
        if depends_on is not None:
            self.depends_on = depends_on
        if parents is not None:
            self.parents = parents
        else:
            self.parents = [] # TMP !
        # if self.parents is None and isinstance(self.depends_on, set):
        #         raise UnitConfigError("Unit parents are not specified. Can't "
        #                               "use dependencies because it's a set.")
        self.state = '-'

    def _get_dependencies(self, registry):
        container = type(self.depends_on) # todo forbid iterator

        def iterate():
            for dep in self.depends_on:
                if isinstance(dep, type) and issubclass(dep, AppUnit):
                    dep = dep()
                if dep.identity in registry:
                    yield registry[dep.identity]
                else:
                    dep.Prepare(self)
                    yield dep

        self.depends_on = container(iterate())
        yield from self.depends_on

    '''
    @property
    def depends_on(self):
    '''

    autopilot = True

    def Prepare(self, master_unit):
        common_parents = (p for p in master_unit.parents
                          if p.share_context)
        self.parents.extend(common_parents)

    def prepare(self):
        # TODO comments

        all_deps = {}
        ignore = set()

        # Breadth-first iteration:
        def get_deps(unit):
            if unit.identity in ignore:
                return
            yield from unit._get_dependencies(all_deps)

        # rename: unit_by_name
        iter_deps = breadth_first(self, get_deps)
        next(iter_deps) # skip the root
        for dep in iter_deps:
            if dep.identity in all_deps:
                ignore.add(dep.identity)
            else:
                all_deps[dep.identity] = dep

        deps_dict = {dep.identity: tuple(d.identity for d in dep.depends_on)
                     for dep in all_deps.values()}

        class UnitsOrder:
            def __init__(self, unit):
                self.unit = unit

            def __lt__(self, other):
                this = self.unit
                for units in [u.depends_on for u in all_deps.values()]:
                    try:
                        units.index
                    except AttributeError:
                        # most likely, a set
                        continue
                    if this in units and other in units:
                        return units.index(this) < units.index(other)

        def units():
            for units_set in sort_by_deps(deps_dict):
                yield from sorted(units_set, key=UnitsOrder)

        units = [all_deps[name] for name in units()] + [self]

        for unit in units:
            # assert all(dep.state == 'prepared' for dep in unit.deps)
            deps_of_deps = {d.identity for dep in unit.depends_on
                            for d in dep.deps.values()
                            if dep.autopilot}
            unit.deps = deps_of_deps | {dep.identity for dep in unit.depends_on}
            unit.deps = sorted((all_deps[name] for name in unit.deps),
                               key=units.index)
            unit.deps = OrderedDict((d.identity, d) for d in unit.deps)
            unit.parents = [unit.deps.get(p, p) for p in unit.parents]
            unit.__pro__ = unit.get_pro()
            unit.state = 'prepared'

    def get_pro(self):
        return _mro(self.parents,
                    lambda obj: getattr(obj, '__pro__', ()))

    @classmethod
    def make(cls, *args, **kwargs):
        unit = cls(*args, **kwargs)
        unit.prepare()
        return unit

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
        return iter(self.deps.values())

    def autorun(self, stop_after=None):
        # define the start point
        for dep in self:
            dep.result = dep.autorun()
            if dep.identity == stop_after:
                break

    def run(self, stop_after=None):
        '''Can be overriden'''
        self.autorun(stop_after)
    # TODO!! detect cycles & invalid config

    #App.make(*args)

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
