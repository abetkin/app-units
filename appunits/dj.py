from functools import update_wrapper, wraps, partial
from copy import copy

from .base import AppUnit
from .util import NOT_SET

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
        if current_unit is not None:
            self.current_unit = self.unit.all_units[current_unit]
        else:
            self.current_unit = self.unit

    def go(self, unit):
        if (self.all_units.index(self.current_unit)
                > self.all_units.key_index(unit)):
            return self.repeat(unit=unit)
        self.unit.run(stop_after=unit)
        self.current_unit = self.all_units[unit]
        return self

    def __getattr__(self, name):
        return getattr(self.current_unit, name)

    def _repr_pretty_(self, p, cycle):
        # black magic
        from IPython.lib import pretty
        if cycle:
            p.text('UnitsIterator(..)')
            return
        max_length = max(len("%d %s" % (i, str(unit)))
                for i, unit in enumerate(self.all_units))
        def print_units(p, units_enum):
            with p.group(2):
                for i, unit in units_enum:
                    p.break_()
                    id_and_name = ("%d %s" % (i, str(unit))
                            ).ljust(max_length + 1)
                    p.text(id_and_name)
                    with p.group(len(id_and_name)):
                        if unit.result is NOT_SET:
                            result = '-'
                        else:
                            result = pretty.pretty(unit.result)
                        if len(result) > 120:
                            result = '%s(...)' % unit.result.__class__.__name__
                        p.text(result)
        all_units = enumerate(self.all_units)
        current = self.all_units.index(self.current_unit)
        def units_run():
            for i, unit in all_units:
                yield i, unit
                if i == current:
                    break
        p.text('Units run:')
        print_units(p, list(units_run()))

        units_to_run = list(all_units)
        if units_to_run:
            p.break_()
            p.text('Units to run:')
            print_units(p, units_to_run)


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
            unit = copy(self)
            is_test_client = 'units.stop_after' in request.META
            if is_test_client:
                kwargs.update(stop_after=request.META['units.stop_after'])
            unit.run(request, *args, **kwargs)
            if is_test_client:
                # HttpResponse hasn't been got yet
                empty = UnitResponse()
                empty._unit = unit
                return empty
            return unit.result

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

    def main(self):
        return self.view(self.request, *self.view_args, **self.view_kwargs)
