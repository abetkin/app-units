from functools import update_wrapper

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

    @classmethod
    def as_view(cls, *unit_args, **unit_kwargs):

        def view(request, *args, **kwargs):
            view_unit = cls(*unit_args, **unit_kwargs)
            view_unit.request = request
            view_unit.args = args
            view_unit.kwargs = kwargs
            view_unit.prepare()
            return view_unit.autorun(request, *args, **kwargs)

        # take name and docstring from class
        update_wrapper(view, cls, updated=())
        # and possible attributes from run
        update_wrapper(view, cls.run, assigned=())
        return view


# class A:

#     def aa(self):
#         return self


# class Method:

#     def __get__(self, inst, owner):

#         def f():
#             return 3
#         return f


# class B(A):

#     def unit_conf(self):
#         1

#     @UnitDispatch(unit_conf) # kw or callable
#     def dispatch(self, r):
#         1
