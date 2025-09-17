from django.urls import path
from . import views

urlpatterns = [
    path('pc/', views.pc, name= 'pc'),
    path('xemthongso/', views.xemthongso, name= 'xemthongso'),
    path('manhinhxanhpc/', views.manhinhxanhpc, name= 'manhinhxanhpc'),
    path('khongmangpc/', views.khongmangpc, name= 'khongmangpc'),
    path('khonglenman/', views.khonglenman, name= 'khonglenman'),
    path('khongbatduoc/', views.khongbatduoc, name= 'khongbatduoc'),
    path('hoanchinh/', views.hoanchinh, name= 'hoanchinh'),
    path('giatlag/', views.giatlag, name= 'giatlag'),
]