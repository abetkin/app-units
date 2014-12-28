# coding: utf-8
import json

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse

from rest_framework import generics

from appunits import AppUnit, UnitsRunner

class Filter(AppUnit):
    1

class Serialize(AppUnit):
    1

class AppAwareView(View):

    app_units = ()

    def dispatch(self, request, *args, **kwargs):
        app_units = (self,) + tuple(self.app_units)
        app_runner = UnitsRunner(self.app_units)
        app_runner.run()
        self.apps = app_runner.all_units
        return super(AppAwareView, self).dispatch(request, *args, **kwargs)


class ShowCats(AppAwareView):

    app_units = (Filter, Serialize)

    def get(self, request):
        resp = json.dumps(self.apps[Serialize].result)
        return HttpResponse(resp)