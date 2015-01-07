import inspect
from functools import partial
from collections import OrderedDict
from itertools import chain


from .util.mro import _mro
from .util.deps import sort_by_deps, breadth_first, depth_first

from .marks import CollectMarksMeta

class UnitConfigError(Exception):
    pass


# TODO states: prepared, app1, app2, ...
# TODO ability to specify order manually!!
# incapsulation!
# option: ignore warnings

from enum import Enum

class State(Enum):
    CREATED = 0
    PREPARED = 1
    SUCCESS = 2
    FAILED = 2

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
        self.state = State.CREATED

    # @property
    # def depends_on(self):

    autorun_dependencies = True

    def prepare_hook(self, master_unit):
        common_parents = (p for p in master_unit.parents
                          if getattr(p, 'share_context', False))
        self.parents.extend(common_parents)

    def prepare(self):
        # Get a non-ordered list of all units:

        all_units = {}
        ignore = set()
        created = set()

        def instantiate_deps(unit):
            # "get child nodes" function that will be applied to tree nodes
            # in order to iterate it breadth-first.
            if unit.identity in ignore:
                return
            container = type(unit.depends_on) # todo forbid iterator
            def it():
                for dep in unit.depends_on:
                    if isinstance(dep, type) and issubclass(dep, AppUnit):
                        dep = dep()
                    if dep.identity in all_units:
                        dep = all_units[dep.identity]
                    created.add((dep, unit))
                    yield dep
            unit.depends_on = container(it())
            yield from unit.depends_on


        iter_deps = breadth_first(self, instantiate_deps)
        next(iter_deps) # skip the root
        for dep in iter_deps:
            if dep.identity in all_units:
                ignore.add(dep.identity)
            else:
                all_units[dep.identity] = dep

        # Post-create actions:

        for unit, _ in created | {(self, None)}:
            if unit.parents is None:
                unit.parents = list(unit.depends_on)
            else:
                unit.parents = [all_units.get(p, p) for p in unit.parents]
        for unit, master_unit in created:
            unit.prepare_hook(master_unit)

        # Get an ordered list of all units:

        deps_dict = {dep.identity: tuple(d.identity for d in dep.depends_on)
                     for dep in all_units.values()}

        class UnitsOrder:
            def __init__(self, unit):
                self.unit = unit

            def __lt__(self, other):
                this = self.unit
                for units in [u.depends_on for u in all_units.values()]:
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

        all_units = OrderedDict((name, all_units[name]) for name in units())
        all_units[self.identity] = self

        # Set every unit's dependencies:

        for unit in all_units.values():
            assert all(dep.state == State.PREPARED for dep in unit.depends_on)
            unit.all_units = all_units
            def deps_of_deps():
                for u in unit.depends_on:
                    for dep in u.deps.values():
                        if not u.autorun_dependencies and dep in u.depends_on:
                            continue
                        yield dep.identity

            unit.deps = set(deps_of_deps()) | {
                    dep.identity for dep in unit.depends_on}
            units_order = tuple(all_units.keys())
            unit.deps = sorted(unit.deps, key=units_order.index)
            unit.deps = OrderedDict((name, all_units[name]) for name in unit.deps)
            unit.__pro__ = unit.get_pro()
            unit.state = State.PREPARED

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

    def autorun(self, stop_after=None):
        for dep in chain(self.deps.values(), [self]):
            if stop_after:
                all_units = tuple(self.all_units.keys())
                if all_units.index(dep.identity) > all_units.index(stop_after):
                    break
            if dep.state == State.PREPARED:
                dep.result = dep.run()
                dep.state = State.SUCCESS

    def run(self):
        '''Can be overriden'''
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
