from .util.mro import _mro
from .util.deps import sort_by_deps, breadth_first

from functools import partial

# class ClassIdentity(object):

#     def __init__(self, cls):
#         self.cls = cls

#     def __str__(self):
#         return self.cls.__name__

#     def __hash__(self):
#         return hash(self.cls)

#     def __eq__(self, other):
#         if isinstance(other, ClassIdentity):
#             return self.cls == other.cls
#         return self.cls == other

#     __repr__ = __str__


def instantiate(units):
    return [unit() if isinstance(unit, type) else unit
            for unit in units]

# TODO remove
class UnitsRunner(object):

    def __init__(self, units):
        self.units = {u.identity: u for u in instantiate(units)}

    def traverse_deps(self):
        '''
        breadth-first
        '''

        def deps_dict():
            for name, unit  in tuple(self.units.items()):
                def deps():
                    for dep in unit.get_deps():
                        self.units.setdefault(dep.identity, dep) # TOTO process deps
                        yield dep.identity
                yield name, list(deps())

        deps_dict = dict(deps_dict())

        def ordered_units():
            for units in sort_by_deps(deps_dict):
                yield from units

        return {id: self.units[id] for id in ordered_units()}

    def __getitem__(self, identity):
        index = self.units.index(identity)
        return self.units[index]


    def run(self):
        self.all_units = self.prepare()
        # TODO error handling
        for name, unit in self.all_units.items():
            # try:

            unit()
            # finally:
            #     print("App: %s" % unit.identity)


class AppUnit(object):
    '''
    '''

    deps = ()
    parents = None

    # app should create its dependencies

    # possibility to add global deps
    def __init__(self, identity=None, deps=None, parents=None):
        #FIXME do not instantiate
        if identity is not None:
            self.identity = identity
        else:
            self.identity = self.__class__
        if deps is not None:
            self.deps = deps
        self.deps = instantiate(self.deps)
        if parents is not None:
            self.parents = parents
        if self.parents is None:
            self.parents = self.deps
        else:
            self.parents = instantiate(self.parents)

    # names only
    # def get_deps(self, result=None):

    #     if result is None:
    #         result = []
    #     for unit in self.deps:
    #         if unit in result:
    #             # TODO forbid units with the same identity
    #             continue
    #         result.append(unit)
    #         unit.get_deps(result)
    #     return result

    # TODO be able exclude context from some apps

    def _create_deps(self, already_created):
        # take iden. into account, stateful
        if self.identity in already_created:
            return iter(())
        return iter(self.deps)

    def traverse_deps(self):
        registry = set()
        get_children = partial(AppUnit._get_deps, registry=registry)
        breadth_first(self, get_children)

    def get_pro(self):
        return _mro(self.parents,
                    lambda obj: getattr(obj, '__pro__', ()))

    def run(self):
        raise NotImplementedError()

    def __repr__(self):
        return 'Unit %s' % repr(self.identity)

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
