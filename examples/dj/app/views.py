# coding: utf-8
import json

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse, JsonResponse

from rest_framework import generics, serializers

from appunits import AppUnit, ContextAttribute
from appunits.dj import ViewUnit
from .models import Cat
from appunits.marks import Mark

class Filter(AppUnit):
    1

class Serialize(AppUnit):
    data = ContextAttribute('data')

    COLLECT_INTO = '_declared_fields'
    Mark.register(serializers.Field)

    def get_object(self):
        class srlzer_class(serializers.Serializer):
            pass
        srlzer_class._declared_fields = self._declared_fields
        srlzer = srlzer_class(data=self.data)
        if srlzer.is_valid():
            return srlzer.data
        return srlzer.errors

    def run(self):
        return self.get_object()


class CatSerializer(Serialize):
    data = ContextAttribute('request.GET')

    name = serializers.CharField()
    happy = serializers.BooleanField()


class AppAwareView(View):

    app_units = ()
    publish_attrs = ('request_params',)
    share_context = True

    @property
    def request_params(self):
        return self.request.GET


    def dispatch(self, request, *args, **kwargs):
        self.app = AppUnit.make('main', self.app_units, [self])
        self.app.autorun()
        return super(AppAwareView, self).dispatch(request, *args, **kwargs)


class ViewCats(ViewUnit):

    # @property
    # def depends_on(self):
    #     return [
    #         Serialize(context_objects=[{'data': self.request.GET}]),
    #     ]
    depends_on = [CatSerializer]

    def run(self, request):
        obj = self.deps[CatSerializer].result
        return JsonResponse(obj)

view_cats = ViewCats.as_view()

class Viu(View):

    # @property
    # def depends_on(self):
    #     return [
    #         Serialize(context_objects=[{'data': self.request.GET}]),
    #     ]
    @ViewCats()
    def dispatch(self, request):
        obj = Viu.dispatch.deps[CatSerializer].result
        return JsonResponse(obj)


viu = Viu.as_view()


class ShowCats(AppAwareView):

    app_units = (Serialize,)

    def get(self, request):
        obj = self.app.deps[Serialize].result
        return JsonResponse(obj)

show_cats = ShowCats.as_view()
