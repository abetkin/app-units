# coding: utf-8
import json

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse, JsonResponse

from rest_framework import generics, serializers

from appunits import AppUnit, ContextAttribute

class Filter(AppUnit):
    1

class Serialize(AppUnit):
    data = ContextAttribute('request_params')

    class _Serializer(serializers.Serializer):
        name = serializers.CharField()
        happy = serializers.BooleanField()

    def get_object(self):
        srlzer = self._Serializer(data=self.data)
        if srlzer.is_valid():
            return srlzer.data

    def run(self):
        return self.get_object()


class AppAwareView(View):

    app_units = ()
    published_context = ('request_params',)
    share_context = True

    @property
    def request_params(self):
        return self.request.GET


    def dispatch(self, request, *args, **kwargs):
        self.app = AppUnit.make('main', self.app_units, [self])
        self.app.autorun()
        return super(AppAwareView, self).dispatch(request, *args, **kwargs)


class ShowCats(AppAwareView):

    app_units = (Serialize,)

    def get(self, request):
        obj = self.app.deps[Serialize].result
        return JsonResponse(obj)

show_cats = ShowCats.as_view()
