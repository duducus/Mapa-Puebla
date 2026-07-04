from django.urls import path
from . import views

urlpatterns = [
    path('',                views.index,        name='index'),
    path('api/geojson/',    views.geojson_api,  name='geojson'),
    path('api/distritos/',  views.distritos_api, name='distritos'),
]
