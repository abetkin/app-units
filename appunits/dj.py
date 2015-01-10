from functools import update_wrapper, wraps, partial
import types

from .base import AppUnit

from django import test
from django.http import HttpResponse

class UnitClient(test.Client):

    def generic(self, method, path, **kw):
        stop_after = kw.pop('unit', None)
        repeat = partial(self.generic, method=method, path=path, **kw)
        kw.update({'units.stop_after': stop_after})
        response = super().generic(method, path, **kw)
        return UnitsIterator(response._unit, repeat, stop_after)


class UnitsIterator:

    def __init__(self, unit, repeat, current_unit):
        self.unit = unit
        self.repeat = repeat
        self.current_unit = self[current_unit]

    def go(self, unit):
        all_units = tuple(self.unit.all_units.keys())
        if not isinstance(unit, int):
            unit = all_units.index(unit)
        if all_units.index(self.identity) > unit:
            return self.repeat(unit=unit)
        self.unit.autorun(stop_after=unit)
        self.current_unit = self[unit]
        return self

    def __getattr__(self, name):
        return getattr(self.current_unit, name)

    def _repr_pretty_(self, p, cycle):
        from IPython.lib import pretty
        if cycle:
            p.text('UnitsIterator(..)')
            return
        p.text('Application units:')
        # all_units = tuple()
        # with p.group(2):
        #     self.all_units.index
        #     p.text(self.wrapped_func.__name__) #(a=1,b=..)
        #     p.text(' returned')
        #     p.breakable()
        #     p.text( pretty(self.rv))

    # full info:
    # N# app:\n result
    # To run:\n ..

    def __getitem__(self, unit):
        if unit is None:
            return self.unit
        if isinstance(unit, int):
            return tuple(self.unit.all_units.values())[unit]
        return self.unit.all_units[unit]


class UnitResponse(HttpResponse):
    pass

class ViewUnit(AppUnit):

    view = None

    publish_attrs = ['request']

    def prepare_run(self, request, *args, **kwargs):
        self.request = request
        self.view_args = args
        self.view_kwargs = kwargs

    def as_view(self):
        if not self.view:
            raise NotImplementedError('No "view" callable in %s' % self)

        def view(request, *args, **kwargs):
            is_test_client = 'units.stop_after' in request.META
            if is_test_client:
                kwargs.update(stop_after=request.META['units.stop_after'])
            self.autorun(request, *args, **kwargs)
            if is_test_client:
                # HttpResponse hasn't been got yet
                empty = UnitResponse()
                empty._unit = self
                return empty
            return self.result

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

    def run(self):
        return self.view(self.request, *self.view_args, **self.view_kwargs)
