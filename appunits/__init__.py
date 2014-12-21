from .util.mro import mro

class AppUnit(object):
    
    def __init__(self, deps):
        1


class ContextAttribute:
    '''
    An attribute that is looked up in the context.
    '''

    PUBLISHED_CONTEXT_ATTR = 'published_context'
    PUBLISHED_CONTEXT_EXTRA_ATTR = 'published_context_extra'

    def __init__(self, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance:
            return self._lookup(instance)

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
    


#class PrototypeMixin:
#    published_context = ()

#    def get_from_context(self, attr, *default):
#        for obj in self._objects():
#            if attr in obj.published_context:
#                return getattr(obj, attr)
#            if hasattr(obj, 'published_context_extra') \
#                    and attr in obj.published_context_extra:
#                return obj.published_context_extra[attr]
#        if default:
#            return default[0]k
#        raise AttributeError(attr)

