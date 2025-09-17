from django.urls import path
from . import views 

urlpatterns = [
    path('tichhop/', views.tichhop, name= 'tichhop'),
    path('tvoff/', views.tvoff, name= 'tvoff'),
    path('thietbi/', views.thietbi, name= 'thietbi'),
    path('tatthongbao/', views.tatthongbao, name= 'tatthongbao'),
    path('ngaygio/', views.ngaygio, name= 'ngaygio'),
    path('manhinhxanh/', views.manhinhxanh, name= 'manhinhxanh'),
    path('fileusb/', views.fileusb, name= 'fileusb'),
    path('khongwifi/', views.khongwifi, name= 'khongwifi'),
    path('docamung/', views.docamung, name= 'docamung'),
]