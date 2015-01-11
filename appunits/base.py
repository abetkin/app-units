import inspect
from functools import partial
from collections import OrderedDict
import itertools

from .util import get_attribute, DictAndList, NOT_SET, can_peek
from .util.mro import _mro
from .util.deps import sort_by_deps, breadth_first

from .marks import CollectMarksMeta

class UnitConfigError(Exception):
    pass

class ProChainError(Exception):
    pass

class Unit(metaclass=CollectMarksMeta):
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
        if context_objects is not None:
            self.context_objects = context_objects
        self.result = NOT_SET

    autorun_dependencies = True

    def prepare_unit(self, parents):
        '''
        A hook that can be used, for example,
        for sharing some of the parent's context with the child.
        '''
        to_add = [obj for obj in parents.values()
                  if obj not in self.context_objects]
        if to_add:
            self.context_objects = list(self.context_objects)
            self.context_objects.extend(to_add)

    def prepare_run(self, *args, **kwargs):
        self.run_args = getattr(self, 'run_args', args)
        self.run_kwargs = getattr(self, 'run_kwargs', kwargs)

    def _prepare_run(self, *run_args, **run_kwargs):
        '''TODO what it does? self.all_units ?
        '''
        self.prepare_run(*run_args, **run_kwargs)

        ## Get a non-ordered list of all units ##

        all_units = {} # key = value
        parents = {}

        def instantiate_deps(unit):
            container = type(unit.depends_on) # todo forbid iterator
            def it():
                for dep in unit.depends_on:
                    if isinstance(dep, type) and issubclass(dep, Unit):
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

        all_units = DictAndList((u.identity, u) for u in units())

        ## Set all units' dependencies ##

        for unit in all_units:
            unit.all_units = all_units
            unit_deps = set(unit.deps) if unit.autorun_dependencies else set()
            for dep in unit.deps:
                unit_deps |= set(dep.deps)
            unit.deps = sorted(unit_deps, key=all_units.index)

        # providing a nicer interface
        for unit in all_units:
            unit.deps = DictAndList((u.identity, u) for u in unit.deps)

        ## Set the context objects ##

        for unit, parents in itertools.chain(parents.items(),
                                             [(self, [])]):
            parents = OrderedDict((u.identity, u) for u in parents)
            unit.prepare_unit(parents)
            unit.get_pro()

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
                               partial(Unit.get_pro, chain=chain))
        return obj.__pro__

    def __repr__(self):
        return 'Unit %s' % repr(self.identity)

    def __str__(self):
        if isinstance(self.identity, type):
            return self.identity.__name__
        return str(self.identity)

    def __hash__(self):
        return hash(self.identity)

    def __eq__(self, other):
        if isinstance(other, Unit):
            return self.identity == other.identity

    # Recursion should happen only when traversing
    #

    def run(self, *args, stop_after=None, **kwargs):
        if not getattr(self, 'run_session', None):
            self._prepare_run(*args, **kwargs)

            def iter_units():
                yield from self.deps
                yield self
            self.run_session = can_peek(iter_units())

        if stop_after is not None:
            next_unit = self.run_session.peek()
            if self.all_units.index(next_unit) \
                    > self.all_units.key_index(stop_after):
                raise StopIteration()

        for unit in self.run_session:
            unit.result = unit.main()
            if stop_after is None:
                continue
            try:
                next_unit = self.run_session.peek()
            except StopIteration:
                return
            if self.all_units.index(next_unit) \
                    > self.all_units.key_index(stop_after):
                return


    def main(self):
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
