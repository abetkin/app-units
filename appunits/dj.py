from functools import update_wrapper, wraps
import types

from .base import AppUnit

from django import test

class UnitClient(test.Client):

    def generic(self, method, path, **kw):
        response = super().generic(method, path, **kw)
        return UnitResponse(response)


class UnitResponse:

    def __init__(self, http_resp):
        self.main_unit = http_resp._unit


class ViewUnit(AppUnit):

    view = None

    publish_attrs = ['request']

    def as_view(self):
        if not self.view:
            raise NotImplementedError('No "view" callable in %s' % self)

        def view(request, *args, **kwargs):
            self.request = request
            self.prepare()
            return self.autorun(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, self.__class__, updated=())
        # and possible attributes from the view function
        update_wrapper(view, self.view, assigned=())
        return view

    def __get__(self, instance, owner):
        if instance is None:
            return self
        decorated = getattr(self, '_decorated_func', None)
        dispatch = decorated.__get__(instance) if decorated \
                else super(owner, instance).dispatch
        self.view = dispatch
        return self.as_view()

    def __call__(self, f):
        self._decorated_func = f
        return self

    def run(self, request, *args, **kwargs):
        return self.view(request, *args, **kwargs)
