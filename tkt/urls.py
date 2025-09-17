"""
URL configuration for tkt project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import  settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500
#from . import consumers
urlpatterns = [
    path('', include('eeror.urls')),
    path('dashboard', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('admin/', admin.site.urls),
    path('ticket/', include('ticket.urls')),
    path('box/', include('box.urls')),
    path('touch/', include('touch.urls')),
    path('computer/', include('computer.urls')),
    path('internet/', include('internet.urls')),
    path('todo/', include('todo.urls')),
    path('asset/', include('asset.urls')),
]
#websocket_urlpatterns = [
    #path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
#]
admin.site.site_header = 'Ensipre Error'
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'accounts.views.custom_404'
handler500 = 'accounts.views.custom_500'
