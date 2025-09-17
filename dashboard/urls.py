from django.urls import path
from . import views 

urlpatterns = [
    path('dashboard', views.dashboard, name = 'dashboard'),
    path('todo_dashboard', views.todo_dashboard, name = 'todo_dashboard')
]
