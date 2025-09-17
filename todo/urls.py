from django.urls import path
from . import views

urlpatterns = [
    path('create_todo_list/', views.create_todo_list, name = 'create_todo_list'),
    path('todo_list_details/<str:todo_list_id>/', views.todo_list_details, name = 'todo_list_details'),
    path('active_todo_list/', views.active_todo_list, name = 'active_todo_list'),
    path('resolved_todo_list/', views.resolved_todo_list, name = 'resolved_todo_list'),
    path('view_todo_list/', views.view_todo_list, name = 'view_todo_list'),
    path('todo_list/<str:todo_list_id>/edit_task_list/<str:task_list_id>/', views.edit_task_list, name='edit_task_list'),
    path('todo_list/<str:todo_list_id>/delete_task/<str:task_list_id>/', views.delete_task_list, name='delete_task_list'),
    path('add_task/', views.AddTaskView.as_view(), name='add_task'),
    path('update_task_status/<str:todo_list_id>/<str:task_list_id>/', views.update_task_status, name='update_task_status'),
    path('resolve_todo_list/<str:todo_list_id>', views.resolve_todo_list, name='resolve_todo_list'),
    path('delete_todo_list/<str:todo_list_id>', views.delete_todo_list, name='delete_todo_list'),
    path('delete_todo_list_details/<str:todo_list_id>', views.delete_todo_list_details, name='delete_todo_list_details'),
    path('delete_todo_list_resolved/<str:todo_list_id>', views.delete_todo_list_resolved, name='delete_todo_list_resolved'),
    path('search_todo_list/', views.search_todo_list, name='search_todo_list'),
    path('delete_todo_list_search/<str:todo_list_id>', views.delete_todo_list_search, name='delete_todo_list_search'),
    path('edit_todo_list/<str:todo_list_id>/', views.edit_todo_list, name='edit_todo_list'),
]
