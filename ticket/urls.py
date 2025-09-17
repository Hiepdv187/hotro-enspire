from django.urls import path
from . import views, consumers
from .views import TicketListCreateView, TicketList

urlpatterns = [
    path('create_ticket/', views.create_ticket, name='create_ticket'),
    path('customer_active_tickets/', views.customer_active_tickets, name='customer_active_tickets'),
    path('customer_resolved_tickets/', views.customer_resolved_tickets, name='customer_resolved_tickets'),
    path('assign_ticket/<str:ticket_id>/', views.assign_ticket, name='assign_ticket'),
    path('add_comment/<str:ticket_id>/', views.add_comment, name='add_comment'),
    path('ticket_details/<str:ticket_id>/', views.ticket_details, name='ticket_details'),
    path('ticket_queue/', views.ticket_queue, name='ticket_queue'),
    path('engineer_active_tickets/', views.engineer_active_tickets, name='engineer_active_tickets'),
    path('engineer_resolved_tickets/', views.engineer_resolved_tickets, name='engineer_resolved_tickets'),
    path('resolve_ticket/<str:ticket_id>/', views.resolve_ticket, name='resolve_ticket'),
    path('admin_active_tickets/', views.admin_active_tickets, name='admin_active_tickets'),
    path('admin_resolved_tickets/', views.admin_resolved_tickets, name='admin_resolved_tickets'),
    path('search/', views.search_tickets, name='search_tickets'),
    path('admin_create_ticket/', views.admin_create_ticket, name='admin_create_ticket'),
    path('ticket/add_reply/<str:ticket_id>/<int:comment_id>/', views.add_reply, name='add_reply'),
    path('comment/delete/<str:comment_id>/', views.delete_comment, name='delete_comment'),
    path('delete_ticket/<str:ticket_id>/', views.delete_ticket, name='delete_ticket'),
    path('admin_view_tickets/', views.admin_view_tickets, name='admin_view_tickets'),
    path('engineer_view_tickets/', views.engineer_view_tickets, name='engineer_view_tickets'),
    path('customer_view_tickets/', views.customer_view_tickets, name='customer_view_tickets'),
    path('change_assign_ticket/<str:ticket_id>/', views.change_assign_ticket, name='change_assign_ticket'),
    path('edit_ticket/<str:ticket_id>/', views.edit_ticket, name='edit_ticket'),
    path('change_assign_ticket_view/<str:ticket_id>/', views.change_assign_ticket_view, name='change_assign_ticket_view'),
    path('assign_ticket_view/<str:ticket_id>/', views.assign_ticket_view, name='assign_ticket_view'),
    path('delete_ticket_details/<str:ticket_id>', views.delete_ticket_details, name='delete_ticket_details'),
    path('get-notifications/', views.get_notifications, name='get-notifications'),
    path('mark-notification-as-read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('mark-all-notifications-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_read'),
    path('api/tickets/', TicketList.as_view(), name='ticket-list'),
]
websocket_urlpatterns = [
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]