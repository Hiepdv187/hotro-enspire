from django.urls import path
from . import views
urlpatterns = [
    path('tvbox/', views.tvbox, name= 'tvbox'),
    path('usbbox/', views.usbbox, name= 'usbbox'),
    path('sudungoff/', views.sudungoff, name= 'sudungoff'),
    path('roi/', views.roi, name= 'roi'),
    path('phukien/', views.phukien, name='phukien'),
    path('nhieu/', views.nhieu, name= 'nhieu'),
    path('ngaytvbox/', views.ngaytvbox, name= 'ngaytvbox'),
    path('khonglen/', views.khonglen, name= 'khonglen'),
    path('ketnoi/', views.ketnoi, name= 'ketnoi'),
    path('dophangiai/', views.dophangiai, name= 'dophangiai'),
    path('camung/', views.camung, name= 'camung' ),
]