import inspect
from functools import partial
from collections import OrderedDict
import itertools

from .util import get_attribute
from .util.mro import _mro
from .util.deps import sort_by_deps, breadth_first

from .marks import CollectMarksMeta

class UnitConfigError(Exception):
    pass

class ProChainError(Exception):
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
    context_objects = ()

    def __init__(self, identity=None, depends_on=None, context_objects=None):
        if identity is not None:
            self.identity = identity
        else:
            self.identity = self.__class__
        if depends_on is not None:
            self.depends_on = depends_on
        # elif not hasattr(self, 'depends_on'):
        #     self.depends_on = []
        if context_objects is not None:
            self.context_objects = context_objects
        # elif not hasattr(self, 'context_objects'):
        #     self.context_objects = []
        self.state = State.CREATED

    autorun_dependencies = True

    def prepare_hook(self, parents):
        '''
        A hook that can be used, for example,
        for sharing some of the parent's context with the child.
        '''
        self.context_objects = list(self.context_objects)
        self.context_objects.extend(parents.values())

    def prepare(self):
        ## Get a non-ordered list of all units ##

        all_units = {} # key = value
        parents = {}

        def instantiate_deps(unit):
            container = type(unit.depends_on) # todo forbid iterator
            def it():
                for dep in unit.depends_on:
                    if isinstance(dep, type) and issubclass(dep, AppUnit):
                        dep = dep()
                    if dep in all_units:
                        dep = all_units[dep]
                    parents.setdefault(dep, []).append(unit)
                    yield dep
            unit.deps = container(it())
            yield from unit.deps

        list(breadth_first(self, instantiate_deps, all_units))

        ## Get an ordered list of all units ##

        deps_dict = {unit: unit.deps for unit in all_units}

        class UnitsOrder:
            def __init__(self, unit):
                self.unit = unit

            def __lt__(self, other):
                this = self.unit
                for units in [u.deps for u in all_units]:
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

        all_units = list(units())
        # providing a nicer interface
        all_units_dict = OrderedDict((u.identity, u) for u in all_units)

        ## Set all units' dependencies ##

        for unit in all_units:
            unit.all_units = all_units_dict
            unit_deps = set(unit.deps) if unit.autorun_dependencies else set()
            for dep in unit.deps:
                unit_deps |= set(dep.deps)
            unit.deps = sorted(unit_deps, key=all_units.index)

        # providing a nicer interface
        for unit in all_units:
            unit.deps = OrderedDict((u.identity, u) for u in unit.deps)

        ## Set the context objects ##

        for unit, parents in itertools.chain(parents.items(),
                                             [(self, [])]):
            parents = OrderedDict((u.identity, u) for u in parents)
            unit.prepare_hook(parents)
            unit.get_pro()
            unit.state = State.PREPARED

        assert all(unit.state == State.PREPARED for unit in all_units)


    def get_pro(obj, chain=None):
        if not getattr(obj, 'context_objects', ()):
            return ()
        if not hasattr(obj, '__pro__'):
            if chain is None:
                chain = []
            elif obj in chain:
                raise ProChainError(chain + [obj])
            else:
                chain.append(obj)
            obj.__pro__ = _mro(obj.context_objects,
                               partial(AppUnit.get_pro, chain=chain))
        return obj.__pro__

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

    def autorun(self, *args, stop_after=None, **kwargs):

        def stop_before(unit):
            if stop_after:
                all_units = tuple(self.all_units.keys())
                return (all_units.index(unit.identity) >
                        all_units.index(stop_after))

        for dep in self.deps.values():
            if stop_before(dep):
                return
            if dep.state == State.PREPARED:
                dep.result = dep.run()
                dep.state = State.SUCCESS

        if stop_before(self):
            return
        if self.state == State.PREPARED:
            self.result = self.run(*args, **kwargs)
            self.state = State.SUCCESS
        return self.result

    def run(self):
        '''Can be overriden'''


    # TODO!! detect cycles & invalid config
    # TODO test units with same deps

class ContextAttribute:
    '''
    An attribute that is looked up in the (parent) context.

    "__pro__" stays for "parent resolution order".
    '''

    def __init__(self, name):
        self.name, *self.rest_of_path = name.split('.')

    def __get__(self, instance, owner):
        if instance:
            obj = self._lookup(instance)
            return get_attribute(obj, self.rest_of_path)
        return self

    def _lookup(self, instance):
        for obj in instance.__pro__:
            publish_attrs = getattr(obj, 'publish_attrs', ())
            if self.name in publish_attrs:
               return getattr(obj, self.name)
            if isinstance(obj, dict):
                lookup = obj.__getitem__
            else:
                lookup = getattr(obj, '__lookup__',
                        lambda name: obj.__lookupdict__[name])
            try:
                return lookup(self.name)
            except (AttributeError, KeyError):
                continue
        raise AttributeError(self.name)



# publish_attrs = ('request', 'view') : inheritance ?

# TODO: dot access attr.attr2
