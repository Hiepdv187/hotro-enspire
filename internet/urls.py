from django.urls import path
from . import views

urlpatterns = [
    path('mang/', views.mang, name= 'mang'),\
    path('mangday/', views.mangday, name= 'mangday'),
    path('thietbimang/', views.thietbimang, name= 'thietbimang'),
    path('modem/', views.modem, name= 'modem'),
    path('wifi/', views.wifi, name= 'wifi'),
]