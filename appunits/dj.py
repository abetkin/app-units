from functools import update_wrapper
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

    @classmethod
    def as_view(cls, *unit_args, **unit_kwargs):

        def view(request, *args, **kwargs):
            view_unit = cls(*unit_args, **unit_kwargs)
            view_unit.request = request
            view_unit.prepare()
            return view_unit.autorun(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())
        # and possible attributes from run
        update_wrapper(view, cls.view, assigned=())
        return view

    def __get__(self, instance, owner):
        if instance is None:
            return self
        decorated = getattr(self, '_decorated_func', None)
        dispatch = decorated.__get__(instance) if decorated \
                else super(owner, instance).dispatch
        def view(request, *args, **kwargs):
            self.request = request
            self.prepare()
            self.autorun(request, *args, **kwargs)
            return dispatch(request, *args, **kwargs)

        update_wrapper(view, owner, updated=())
        update_wrapper(view, dispatch, assigned=())
        return view

    def __call__(self, f):
        self._decorated_func = f
        return self

    def run(self, request, *args, **kwargs):
        if not self.view:
            raise NotImplementedError('No "view" callable in %s' % self)
        return self.view(request, *args, **kwargs)
