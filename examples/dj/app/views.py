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
    request = ContextAttribute('request')

    class _Serializer(serializers.Serializer):
        name = serializers.CharField()
        happy = serializers.BooleanField()

    def get_object(self):
        srlzer = self._Serializer(data=self.request.GET)
        if srlzer.is_valid():
            return srlzer.data

    def main(self):
        return self.get_object()


class AppAwareView(View):

    app_units = ()
    published_context = ('request',)
    propagate = True



    def dispatch(self, request, *args, **kwargs):
        self.app = AppUnit('main', self.app_units, [self])
        self.app.run()
        return super(AppAwareView, self).dispatch(request, *args, **kwargs)


class ShowCats(AppAwareView):

    app_units = (Serialize,)

    def get(self, request):
        obj = self.app.all_deps[Serialize].result
        return JsonResponse(obj)

show_cats = ShowCats.as_view()