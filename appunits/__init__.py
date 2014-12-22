from .util.mro import _mro


class AppUnit(object):

    deps = ()

    def __init__(self, deps=None, identity=None):
        if deps is not None:
            self.deps = deps
        if identity is not None:
            self.identity = identity 
        assert self.identity is not None, "App unit should have an identity."
    
    # FIXME view is always the context

    def _get_parents(self):
        return self.deps # TODO not always

    @staticmethod
    def _get_pro(obj):
        return getattr(obj, '__pro__', ())

    def run(self):
        self.__pro__ = _mro(self._get_parents(), get_mro=self._get_pro())
        return self()

    @classmethod
    def run_units(cls, *units):
        unit = 0
        issubclass(unit, AppUnit)


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
