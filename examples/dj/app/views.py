# coding: utf-8
import json
from collections import OrderedDict

from django.shortcuts import render
from django.views.generic import View
from django.http import HttpResponse, JsonResponse

from rest_framework import generics, serializers

from appunits import Unit, ContextAttribute
from appunits.dj import ViewUnit, unit_dispatch
from .models import Cat
from appunits.marks import Mark

class Filter(Unit):
    1

class Serialize(Unit):
    data = ContextAttribute('data')

    collect_into = '_declared_fields'
    Mark.register(serializers.Field)

    def get_object(self):
        class srlzer_class(serializers.Serializer):
            pass
        srlzer_class._declared_fields = OrderedDict(
            (k,v) for k,v in self._marks.items()
            if isinstance(v, serializers.Field))
        srlzer = srlzer_class(data=self.data)
        if srlzer.is_valid():
            return srlzer.data
        return srlzer.errors

    def main(self):
        return self.get_object()


class CatSerializer(Serialize):
    data = ContextAttribute('request.GET')

    name = serializers.CharField()
    happy = serializers.BooleanField()



class ViewCats(ViewUnit):

    # @property
    # def depends_on(self):
    #     return [
    #         Serialize(context_objects=[{'data': self.request.GET}]),
    #     ]
    depends_on = [CatSerializer]

    def rsfgg(self):
        1

    def view(self, request):
        obj = self.deps[CatSerializer].result
        return JsonResponse(obj)

view_cats = ViewCats.as_view()

class Viu(View):

    # @property
    # def depends_on(self):
    #     return [
    #         Serialize(context_objects=[{'data': self.request.GET}]),
    #     ]
    @unit_dispatch(ViewCats)
    def dispatch(self, request):
        obj = self._unit_.deps[CatSerializer].result
        return JsonResponse(obj)


viu = Viu.as_view()