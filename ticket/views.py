import random
import string
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from .form import CreateTicketForm, AssignTicketForm, TicketForm, AdminCreateTicketForm
from .models  import Ticket, Comments, CommentAuthor, Reply, user_directory_paths
from django.db.models import Q
from .form import CommentForm, ReplyForm, ChangeAssignTicketForm
from accounts.models import User
from django.contrib.auth.decorators import login_required
from channels.layers import get_channel_layer
from io import BytesIO
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.text import slugify
from PIL import Image
from asgiref.sync import async_to_sync
from .untils import send_notification
from django.http import JsonResponse
import json
import redis
from .models import Notification
from django.urls import reverse
from django.utils import timezone, formats
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Ticket
from .serializers import TicketSerializer
from django.core.paginator import Paginator

User = get_user_model()
formatted_time = timezone.localtime(timezone.now())
current_time = formats.date_format(formatted_time, format='DATETIME_FORMAT', use_l10n=True)
print(formatted_time)

def send_notification_to_user(user_id, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'user_{user_id}',
        {
            'type': 'send_notification',
            'message': message
        }
    )

class TicketList(APIView):
    permission_classes = [IsAuthenticated]  # Make sure only authorized users can access the API

    def get(self, request):
        tickets = Ticket.objects.all()
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data)

class TicketListCreateView(APIView):
    """
    API để xem danh sách và tạo ticket.
    """
    permission_classes = [AllowAny]  # Public API

    def get(self, request):
        """Lấy danh sách ticket."""
        tickets = Ticket.objects.all()
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Tạo ticket mới."""
        serializer = TicketSerializer(data=request.data)
        if serializer.is_valid():
            # Chỉ cho phép customer tạo ticket nếu không có engineer
            if not request.data.get('engineer'):
                serializer.save(customer=request.user)
            else:
                # Chỉ admin mới được chỉ định engineer
                if request.user.is_superuser:
                    serializer.save(customer=request.user)
                else:
                    return Response(
                        {"error": "Bạn không có quyền chỉ định engineer."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@login_required
def get_notifications(request):
    user_id = request.user.id
    
    # Lấy thông báo từ cơ sở dữ liệu
    notifications_db = Notification.objects.filter(user_id=user_id).order_by('-created_at')
    
    # Chuyển đổi QuerySet thành danh sách từ điển
    notifications_list = []
    for notification in notifications_db:
        notifications_list.append({
            'id': notification.id,
            'message': notification.message,
            'read': notification.read,
            'timestamp': notification.created_at.strftime('%Y-%m-%dT%H:%M:%S')  # Định dạng datetime thành chuỗi
        })
    
    # Lấy thông báo chưa đọc từ Redis nếu người dùng không online
    if not r.sismember("online_users", user_id):
        notifications_key = f"notifications_{user_id}"
        if r.exists(notifications_key):
            notifications_redis = [json.loads(notification) for notification in r.lrange(notifications_key, 0, -1)]
            # Thêm thông báo từ Redis vào danh sách
            notifications_list.extend(notifications_redis)
            # Xóa các thông báo đã lấy từ Redis để tránh lấy lại lần sau
            r.delete(notifications_key)
    
    # Sắp xếp lại danh sách thông báo theo thời gian mới nhất
    notifications_list.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Giới hạn số lượng thông báo trả về
    notifications_list = notifications_list[:200]

    return JsonResponse(notifications_list, safe=False)

@csrf_exempt
def mark_notification_as_read(request, notification_id):
    if request.method == 'POST':
        try:
            # Lấy thông báo từ cơ sở dữ liệu
            notification = Notification.objects.get(id=notification_id, user=request.user)
            
            # Đánh dấu là đã đọc nếu chưa đọc
            if not notification.read:
                notification.read = True
                notification.save()
                
                # Cập nhật lại số thông báo chưa đọc trong Redis (nếu cần)
                try:
                    r = redis.from_url("redis://:iJuwEuyIQmk9jWX1gWqhnyzJYcwn6TFn@redis-14167.c89.us-east-1-3.ec2.redns.redis-cloud.com:14167/0")
                    unread_count = Notification.objects.filter(user=request.user, read=False).count()
                    r.set(f'user_{request.user.id}_unread_count', unread_count)
                except Exception as e:
                    print(f"Error updating Redis unread count: {e}")
            
            return JsonResponse({
                'status': 'success',
                'notification_id': notification.id,
                'read': True
            }, status=200)
            
        except Notification.DoesNotExist:
            return JsonResponse({'error': 'Không tìm thấy thông báo'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Lỗi server: {str(e)}'}, status=500)
    return JsonResponse({'error': 'Phương thức không hợp lệ'}, status=400)

@login_required
@csrf_exempt
def mark_all_notifications_as_read(request):
    if request.method == 'POST':
        try:
            # Đánh dấu tất cả thông báo chưa đọc là đã đọc
            updated_count = Notification.objects.filter(
                user=request.user,
                read=False
            ).update(read=True)
            
            # Cập nhật lại số thông báo chưa đọc trong Redis
            try:
                r = redis.from_url("redis://:iJuwEuyIQmk9jWX1gWqhnyzJYcwn6TFn@redis-14167.c89.us-east-1-3.ec2.redns.redis-cloud.com:14167/0")
                r.set(f'user_{request.user.id}_unread_count', 0)
            except Exception as e:
                print(f"Error updating Redis unread count: {e}")
            
            return JsonResponse({
                'status': 'success',
                'updated_count': updated_count,
                'message': f'Đã đánh dấu {updated_count} thông báo là đã đọc'
            }, status=200)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Lỗi khi đánh dấu tất cả thông báo: {str(e)}'
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Phương thức không được hỗ trợ'
    }, status=405)

@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = CreateTicketForm(request.POST, request.FILES) 
        superusers = User.objects.filter(is_superuser=True)
        if form.is_valid():
            var = form.save(commit=False)
            var.customer = request.user
            
            while not var.ticket_id:
                id = ''.join(random.choices(string.digits, k=6))
                try:
                    var.ticket_id = id
                    var.save()
                    
                    # Send email confirmation to customer
                    subject = f'{var.ticket_title} #{var.ticket_id}'
                    message = 'Cảm ơn bạn đã gửi yêu cầu, chúng tôi sẽ hỗ trợ sớm nhất có thể!'
                    email_from = 'hiep18797@gmail.com'
                    recipient_list = [request.user.email]
                    send_mail(subject, message, email_from, recipient_list)
                    
                    # Send notifications to all superusers
                    ticket_url = request.build_absolute_uri(
                        reverse('ticket_details', kwargs={'ticket_id': var.ticket_id})
                    )
                    ticket_created_on = naturaltime(timezone.now())
                    
                    for superuser in superusers:
                        # Create notification in database
                        notification = Notification.objects.create(
                            user=superuser,
                            message=f'<a href="{ticket_url}">{var.customer.get_full_name()} đã tạo phiếu yêu cầu #{var.ticket_id}</a>',
                            read=False
                        )
                        
                        # Send real-time notification
                        from .untils import send_notification
                        send_notification(
                            superuser.id,
                            f'<a href="{ticket_url}">{var.customer.get_full_name()} đã tạo phiếu yêu cầu mới #{var.ticket_id}. <small>{ticket_created_on}</small></a>'
                        )
                    
                    break
                except IntegrityError:
                    continue
                except Exception as e:
                    print(f"Error sending notification: {e}")
                    continue
                    
            messages.success(request, 'Yêu cầu của bạn đã được gửi. Bạn sẽ được hỗ trợ sớm nhất có thể.')
            return redirect('customer_active_tickets')
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng nhập lại')
            return redirect('create_ticket')
    else:
        form = CreateTicketForm()
        context = {'form': form}
        return render(request, 'ticket/create_ticket.html', context)

@login_required
def admin_create_ticket(request):
    if request.method == 'POST':
        form = AdminCreateTicketForm(request.POST, request.FILES) 
        superusers = User.objects.filter(is_superuser=True)
        if form.is_valid():
            var = form.save(commit=False)
            var.customer = request.user
            var.is_assigned_to_engineer = True
            var.status = 'Đang xử lý'
            while not var.ticket_id:
                id = ''.join(random.choices(string.digits, k=6))
                try:
                    var.ticket_id = id
                    var.save()
                    subject = f'{var.ticket_title} #{var.ticket_id}'
                    message = 'Cảm ơn bạn đã gửi yêu cầu, chúng tôi sẽ hỗ trợ sớm nhất có thể!'
                    email_from = 'hiep18797@gmail.com'
                    recipient_list = [request.user.email, ]
                    send_mail(subject, message, email_from, recipient_list)
                    break
                except IntegrityError:
                    continue
            admin_created_on = naturaltime(current_time)
            engineer_id = var.engineer.id
            ticket_url = reverse('ticket_details', kwargs={'ticket_id': var.ticket_id})
            message1 = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{var.ticket_id} đã được chuyển đến bạn để hỗ trợ.'"<br>" f'<small>{admin_created_on}</small></a>'
            send_notification(engineer_id, message1)
            messages.success(request, 'Yêu cầu của bạn đã được gửi. Bạn sẽ được hỗ trợ sớm nhất có thể.')
            return redirect('admin_active_tickets')
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng nhập lại')
            return redirect('admin_create_ticket')
    else:
        form = AdminCreateTicketForm()
        form.fields['engineer'].queryset = User.objects.filter(is_engineer = True)
        context = {'form': form}
        return render(request, 'ticket/admin_create_ticket.html', context)
# tất cả ticket đã được tạo
@login_required
def customer_active_tickets(request):
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Base queryset
    tickets = Ticket.objects.filter(customer=request.user, is_resolved=False).select_related('customer', 'engineer')
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = tickets.count()
    closed_tickets = Ticket.objects.filter(customer=request.user, is_resolved=True).count()
    tickets_count = active_tickets + closed_tickets
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': tickets_count,
    }
    return render(request, 'ticket/customer_active_tickets.html', context)

@login_required
def customer_resolved_tickets(request):
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Base queryset
    tickets = Ticket.objects.filter(customer=request.user, is_resolved=True).select_related('customer', 'engineer')
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = Ticket.objects.filter(customer=request.user, is_resolved=False).count()
    closed_tickets = tickets.count()
    tickets_count = active_tickets + closed_tickets
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': tickets_count,
    }
    return render(request, 'ticket/customer_resolved_tickets.html', context)
@login_required
def customer_view_tickets(request):
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Base queryset
    tickets = Ticket.objects.filter(customer=request.user).select_related('customer', 'engineer')
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = tickets.filter(is_resolved=False).count()
    closed_tickets = tickets.filter(is_resolved=True).count()
    tickets_count = tickets.count()
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': tickets_count,
    }
    return render(request, 'ticket/customer_view_tickets.html', context)
@login_required
def engineer_active_tickets(request):
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Base queryset
    tickets = Ticket.objects.filter(engineer=request.user, is_resolved=False).select_related('customer', 'engineer')
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query) |
            Q(customer__username__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = tickets.count()
    closed_tickets = Ticket.objects.filter(engineer=request.user, is_resolved=True).count()
    tickets_count = active_tickets + closed_tickets
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': tickets_count,
    }
    return render(request, 'ticket/engineer_active_tickets.html', context)

@login_required
def engineer_resolved_tickets(request):
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Base queryset
    tickets = Ticket.objects.filter(engineer=request.user, is_resolved=True).select_related('customer', 'engineer')
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query) |
            Q(customer__username__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = Ticket.objects.filter(engineer=request.user, is_resolved=False).count()
    closed_tickets = tickets.count()
    tickets_count = active_tickets + closed_tickets
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': tickets_count,
    }
    return render(request, 'ticket/engineer_resolved_tickets.html', context)
@login_required
def engineer_view_tickets(request):
    # Get search query and status filter
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset
    tickets = Ticket.objects.filter(engineer=request.user).select_related('customer', 'engineer')
    
    # Apply status filter
    if status_filter == 'active':
        tickets = tickets.filter(is_resolved=False)
    elif status_filter == 'resolved':
        tickets = tickets.filter(is_resolved=True)
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query) |
            Q(customer__username__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = Ticket.objects.filter(engineer=request.user, is_resolved=False).count()
    closed_tickets = Ticket.objects.filter(engineer=request.user, is_resolved=True).count()
    tickets_count = active_tickets + closed_tickets
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': tickets_count,
    }
    return render(request, 'ticket/engineer_view_tickets.html', context)
@login_required
def admin_active_tickets(request):
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Base queryset - get all active tickets across the system
    tickets = Ticket.objects.filter(is_resolved=False).select_related('customer', 'engineer')
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(engineer__username__icontains=search_query) |
            Q(engineer__first_name__icontains=search_query) |
            Q(engineer__last_name__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = tickets.count()
    closed_tickets = Ticket.objects.filter(is_resolved=True).count()
    total_tickets = Ticket.objects.count()
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': total_tickets,
    }
    return render(request, 'ticket/admin_active_tickets.html', context)

@login_required
def admin_resolved_tickets(request):
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Base queryset - get all resolved tickets across the system
    tickets = Ticket.objects.filter(is_resolved=True).select_related('customer', 'engineer')
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(engineer__username__icontains=search_query) |
            Q(engineer__first_name__icontains=search_query) |
            Q(engineer__last_name__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = Ticket.objects.filter(is_resolved=False).count()
    closed_tickets = tickets.count()
    total_tickets = Ticket.objects.count()
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': total_tickets,
    }
    return render(request, 'ticket/admin_resolved_tickets.html', context)
@login_required
def admin_view_tickets(request):
    # Get search query
    search_query = request.GET.get('q', '')
    
    # Base queryset - get all tickets across the system
    tickets = Ticket.objects.all().select_related('customer', 'engineer')
    
    # Apply search filter if query exists
    if search_query:
        tickets = tickets.filter(
            Q(ticket_title__icontains=search_query) |
            Q(ticket_description__icontains=search_query) |
            Q(ticket_number__icontains=search_query) |
            Q(customer__username__icontains=search_query) |
            Q(customer__first_name__icontains=search_query) |
            Q(customer__last_name__icontains=search_query) |
            Q(engineer__username__icontains=search_query) |
            Q(engineer__first_name__icontains=search_query) |
            Q(engineer__last_name__icontains=search_query)
        )
    
    # Get counts for stats
    active_tickets = Ticket.objects.filter(is_resolved=False).count()
    closed_tickets = Ticket.objects.filter(is_resolved=True).count()
    total_tickets = Ticket.objects.count()
    
    # Order by created_on (newest first)
    tickets = tickets.order_by('-created_on')
    
    # Add pagination
    paginator = Paginator(tickets, 10)  # Show 10 tickets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # For API response
    if request.headers.get('Accept') == 'application/json' or request.GET.get('format') == 'json':
        serializer = TicketSerializer(tickets, many=True)
        return JsonResponse(serializer.data, safe=False, status=200)
    
    # Get engineers for assign dropdown
    engineers = User.objects.filter(is_engineer=True)
    
    context = {
        'tickets': page_obj,
        'page_obj': page_obj,
        'engineers': engineers,
        'search_query': search_query,
        'active_tickets': active_tickets,
        'closed_tickets': closed_tickets,
        'tickets_count': total_tickets,
    }
    return render(request, 'ticket/admin_view_tickets.html', context)

# giao tickets cho engineers
@login_required
def assign_ticket(request,ticket_id):
    ticket = Ticket.objects.get(ticket_id = ticket_id)
    if request.method == 'POST':
        form = AssignTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            var = form.save(commit=False)
            var.is_assigned_to_engineer = True
            var.status = 'Đang xử lý'
            var.save()
            
            ticket_url = reverse('ticket_details', kwargs={'ticket_id': var.ticket_id})
            customer_id = var.customer.id
            engineer_id = var.engineer.id
            assign_created_on = naturaltime(current_time)
            
            # Notify ticket creator
            message_to_creator = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{var.ticket_id} của bạn đã được chuyển đến {var.engineer.last_name} {var.engineer.first_name} để hỗ trợ.'"<br>" f'<small>{assign_created_on}</small>'
            send_notification(customer_id, message_to_creator)
            
            # Notify assigned engineer
            message_to_engineer = f'<a href="{ticket_url}" target="_blank">Bạn vừa được giao xử lý phiếu yêu cầu #{var.ticket_id} từ {var.customer.last_name} {var.customer.first_name}.'"<br>" f'<small>{assign_created_on}</small>'
            send_notification(engineer_id, message_to_engineer)
            
            # Notify all superusers (admins)
            superusers = User.objects.filter(is_superuser=True)
            for superuser in superusers:
                if superuser.id != request.user.id:  # Don't notify the current user if they're a superuser
                    message_to_admin = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{var.ticket_id} đã được giao cho {var.engineer.last_name} {var.engineer.first_name} xử lý.'"<br>" f'<small>{assign_created_on}</small>'
                    send_notification(superuser.id, message_to_admin)
            
            messages.success(request, f'Phiếu yêu cầu đã được giao cho {var.engineer.last_name} {var.engineer.first_name}')
            return redirect('ticket_queue')
        else:
            messages.warning(request, 'Đã có lỗi xảy ra, xin hãy thử lại.')
            return redirect('assign_ticket') 
    else:
        form = AssignTicketForm(instance=ticket)
        form.fields['engineer'].queryset = User.objects.filter(is_engineer = True)
        context = {'form': form, 'ticket': ticket}
        return render(request, 'ticket/assign_ticket.html', context)
        
@login_required
def change_assign_ticket(request, ticket_id):
    ticket = Ticket.objects.get(ticket_id=ticket_id)
    old_engineer = ticket.engineer  # Lưu lại người xử lý cũ
    
    if request.method == 'POST':
        form = ChangeAssignTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            var = form.save(commit=False)
            var.is_assigned_to_engineer = True
            var.status = 'Đang xử lý'
            var.save()
            
            ticket_url = reverse('ticket_details', kwargs={'ticket_id': var.ticket_id})
            new_engineer_id = var.engineer.id
            customer_id = var.customer.id
            change_assign_created_on = naturaltime(current_time)
            
            # Thông báo cho kỹ thuật viên mới
            if old_engineer and old_engineer.id != new_engineer_id:
                message_to_new_engineer = f'<a href="{ticket_url}" target="_blank">Bạn vừa được giao xử lý phiếu yêu cầu #{var.ticket_id} từ {var.customer.last_name} {var.customer.first_name}.'"<br>" f'<small>{change_assign_created_on}</small>'
                send_notification(new_engineer_id, message_to_new_engineer)
                
                # Thông báo cho kỹ thuật viên cũ (nếu có và khác với người mới)
                if old_engineer and old_engineer.id != request.user.id:  # Không thông báo nếu người dùng tự thay đổi
                    message_to_old_engineer = f'<a href="{ticket_url}" target="_blank">Bạn đã được chuyển quyền xử lý phiếu yêu cầu #{var.ticket_id} cho {var.engineer.last_name} {var.engineer.first_name}.'"<br>" f'<small>{change_assign_created_on}</small>'
                    send_notification(old_engineer.id, message_to_old_engineer)
            
            # Thông báo cho người tạo phiếu
            if var.customer.id != request.user.id:  # Không thông báo nếu người tạo là người thực hiện thay đổi
                message_to_customer = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{var.ticket_id} của bạn đã được chuyển cho {var.engineer.last_name} {var.engineer.first_name} xử lý.'"<br>" f'<small>{change_assign_created_on}</small>'
                send_notification(customer_id, message_to_customer)
            
            # Thông báo cho tất cả quản trị viên
            superusers = User.objects.filter(is_superuser=True)
            for superuser in superusers:
                if superuser.id != request.user.id:  # Không thông báo cho người đang thực hiện thay đổi nếu là admin
                    message_to_admin = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{var.ticket_id} đã được chuyển từ {old_engineer.last_name if old_engineer else "chưa có người xử lý"} sang {var.engineer.last_name} {var.engineer.first_name}.'"<br>" f'<small>{change_assign_created_on}</small>'
                    send_notification(superuser.id, message_to_admin)
            
            messages.success(request, f'Phiếu yêu cầu đã được chuyển cho {var.engineer.last_name} {var.engineer.first_name} xử lý')
            return redirect('ticket_details', ticket_id=ticket_id)
        else:
            messages.warning(request, 'Đã có lỗi xảy ra, xin hãy thử lại.')
            return redirect('change_assign_ticket')
    else:
        form = ChangeAssignTicketForm(instance=ticket)
        form.fields['engineer'].queryset = User.objects.filter(is_engineer=True)
        context = {'form': form, 'ticket': ticket}
        return render(request, 'ticket/change_assign_ticket.html', context)

def notify_engineer_about_comment(comment, ticket, ticket_id):
    engineer = ticket.engineer
    noti_time = naturaltime(current_time)
    ticket_url = reverse('ticket_details', kwargs={'ticket_id': ticket_id})
    if engineer:
        notification_message = f'<a href="{ticket_url}" target = "_blank">Phiếu #{ticket_id} có một bình luận mới từ {comment.author.name}.'"<br>" f'<small>{noti_time}</small></a>'
        send_notification(engineer.id, notification_message)

def notify_engineer_about_reply(reply, ticket, ticket_id):
    if ticket.is_assigned_to_engineer:
        engineer = ticket.engineer
    noti_time = naturaltime(current_time)
    ticket_url = reverse('ticket_details', kwargs={'ticket_id': ticket_id})
    if engineer:
        notification_message = f'<a href="{ticket_url}" target = "_blank">Phiếu #{ticket_id} có một bình luận mới từ {reply.author.name}.'"<br>" f'<small>{noti_time}</small></a>'
        send_notification(engineer.id, notification_message)
@login_required
def handle_ticket_form(request, ticket, edit_mode=False):
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('ticket_details', ticket_id=ticket.id)
    else:
        form = TicketForm(instance=ticket)
    return form
@login_required
def handle_comment_form(request, ticket):
    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        if form.is_valid():
            comment = form.save(commit=False)
            comment_author, created = CommentAuthor.objects.get_or_create(user=request.user)
            comment.author = comment_author
            comment.ticket = ticket

            # Xử lý tệp ảnh nếu có
            if 'image' in request.FILES:
                image = request.FILES['image']
                image_name = user_directory_paths(comment, image.name)
                image_path = default_storage.save(image_name, ContentFile(image.read()))

                # Resize ảnh nếu cần thiết
                with Image.open(default_storage.path(image_path)) as img:
                    img.thumbnail((300, 300))  # Adjust the size as needed
                    img.save(default_storage.path(image_path))

                comment.image = image_path

            comment.save()
            
            return redirect('ticket_details', ticket_id=ticket.id)
    else:
        form = CommentForm()

    return form
@login_required
def handle_reply_form(request, ticket):
    if request.method == 'POST':
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.author = request.user
            reply.ticket = ticket
            reply.comment = get_object_or_404(Comments, pk=request.POST.get('parent_comment'))
            # Xử lý tệp ảnh nếu có
            if 'image' in request.FILES:
                image = request.FILES['image']
                image_name = user_directory_paths(reply, image.name)
                image_path = default_storage.save(image_name, ContentFile(image.read()))

                # Resize ảnh nếu cần thiết
                with Image.open(default_storage.path(image_path)) as img:
                    img.thumbnail((300, 300))  # Adjust the size as needed
                    img.save(default_storage.path(image_path))

                reply.image = image_path

            reply.save()
            notify_engineer_about_reply(reply, ticket, ticket_id=ticket.ticket_id)
            return redirect('ticket_details', ticket_id=ticket.id)
    else:
        form = ReplyForm()
    return form

@login_required
def ticket_details(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    comments = Comments.objects.filter(ticket=ticket)
    
    comments_form = handle_comment_form(request, ticket)
    edit_form = handle_ticket_form(request, ticket, edit_mode='edit' in request.GET)
    reply_form = handle_reply_form(request, ticket)

    context = {
        'ticket': ticket,
        'comments': comments,
        'comments_form': comments_form,
        'edit_form': edit_form,
        'reply_form': reply_form,
        'edit_mode': 'edit' in request.GET,
    }

    return render(request, 'ticket/ticket_details.html', context)
# sắp xếp ticket
@login_required
def ticket_queue(request):
    tickets = Ticket.objects.filter(is_assigned_to_engineer=False)
    context = {'tickets':tickets}
    return render(request, 'ticket/ticket_queue.html', context)

@login_required
def resolve_ticket(request, ticket_id):
    ticket = Ticket.objects.get(ticket_id=ticket_id)
    superusers = User.objects.filter(is_superuser=True)
    if request.method == 'POST':
        rs = request.POST.get('rs')
        ticket.resolution_steps = rs
        ticket.is_resolved = True
        ticket.status = 'Đã xong'
        ticket.save()
        
        resolved_created_on = naturaltime(current_time)
        ticket_url = reverse('ticket_details', kwargs={'ticket_id': ticket_id})
        
        # Notify ticket creator
        message_to_creator = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{ticket_id} của bạn đã được xử lý bởi {ticket.engineer.last_name} {ticket.engineer.first_name}, hãy kiểm tra lại.</a>'"<br>" f'<small>{resolved_created_on}</small>'
        send_notification(ticket.customer.id, message_to_creator)
        
        # Notify all superusers (admins)
        for superuser in superusers:
            if superuser != request.user:  # Don't notify the current user if they're a superuser
                message_to_admin = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{ticket_id} của {ticket.customer.last_name} {ticket.customer.first_name} đã được xử lý bởi {ticket.engineer.last_name} {ticket.engineer.first_name}.</a>'"<br>" f'<small>{resolved_created_on}</small>'
                send_notification(superuser.id, message_to_admin)
        
        messages.success(request, 'Phiếu đã được xử lý!')
        return redirect('engineer_active_tickets')

@login_required
def search_tickets(request):
    query = request.GET.get('query', '')
    if query.isdigit():
        tickets = Ticket.objects.filter(
            Q(ticket_title__icontains=query) |
            Q(school__icontains=query) |
            Q(ticket_id__icontains=query) |
            Q(engineer__username=query) |  # Thay đổi thành trường phù hợp
            Q(customer__name=query)   # Thay đổi thành trường phù hợp
        )
    else:
        # Trường hợp không phải số nguyên, không thực hiện tìm kiếm theo ticket_id
        tickets = Ticket.objects.filter(
            Q(ticket_title__icontains=query) |
            Q(school__icontains=query) |
            Q(engineer__username=query) |  # Thay đổi thành trường phù hợp
            Q(customer__name=query) |
            Q(status__icontains=query)# Thay đổi thành trường phù hợp
        )
    context = {
        'query': query,
        'tickets': tickets,
    }

    return render(request, 'ticket/search_tickets.html', context)

@login_required
def add_comment(request, ticket_id):
    if request.method == 'POST':
        form = CommentForm(request.POST, request.FILES)
        superusers = User.objects.filter(is_superuser=True)
        if form.is_valid():
            ticket = Ticket.objects.get(ticket_id=ticket_id)

            # Fetch or create CommentAuthor instance
            comment_author, created = CommentAuthor.objects.get_or_create(
                user=request.user, 
                defaults={
                    'name': request.user.get_full_name(), 
                    'avatar': 'media/avatars/{filename}'
                }
            )

            # Create the comment and associate it with the ticket, comment author, and user
            comment = form.save(commit=False)
            comment.ticket = ticket
            comment.author = comment_author
            comment.user = request.user
            comment.save()

            if 'image' in request.FILES:
                image = request.FILES['image']
                image_path = user_directory_paths(comment, image.name)
                
                with default_storage.open(image_path, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)

                # Resize image
                with Image.open(default_storage.path(image_path)) as img:
                    img.thumbnail((300, 300))  # Adjust the size as needed
                    img.save(default_storage.path(image_path))

                comment.image = image_path
                comment.save()
            
            comment_created_on = naturaltime(current_time)
            ticket_url = reverse('ticket_details', kwargs={'ticket_id': ticket_id})
            
            # Thông báo cho người tạo ticket (nếu không phải là người comment)
            if comment_author.user != ticket.customer:
                message_to_creator = f'<a href="{ticket_url}" target="_blank">{comment_author.name} đã bình luận về phiếu #{ticket.ticket_id} của bạn.'"<br>" f'<small>{comment_created_on}</small>'
                send_notification(ticket.customer.id, message_to_creator)
            
            # Thông báo cho kỹ thuật viên được giao (nếu có và không phải là người comment)
            if ticket.engineer and comment_author.user != ticket.engineer:
                message_to_engineer = f'<a href="{ticket_url}" target="_blank">{comment_author.name} đã bình luận về phiếu #{ticket.ticket_id} mà bạn đang xử lý.'"<br>" f'<small>{comment_created_on}</small>'
                send_notification(ticket.engineer.id, message_to_engineer)
            
            # Thông báo cho quản trị viên (trừ người comment nếu họ là admin)
            for superuser in superusers:
                if superuser != request.user:  # Không thông báo cho chính người comment
                    message_to_admin = f'<a href="{ticket_url}" target="_blank">{comment_author.name} đã bình luận về phiếu #{ticket.ticket_id}.'"<br>" f'<small>{comment_created_on}</small>'
                    send_notification(superuser.id, message_to_admin)
            
            return redirect('ticket_details', ticket_id=ticket.ticket_id)
    else:
        form = CommentForm()

    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))



@login_required
def add_reply(request, ticket_id, comment_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)
    comment = get_object_or_404(Comments, pk=comment_id, ticket=ticket)
    superusers = User.objects.filter(is_superuser=True)
    
    if request.method == 'POST':
        reply_form = ReplyForm(request.POST, request.FILES)
        
        if reply_form.is_valid():
            reply = reply_form.save(commit=False)
            reply.ticket = ticket
            reply.comment = comment
            reply.author = request.user
            reply.save()

            # Xử lý tệp ảnh nếu có
            if 'image' in request.FILES:
                image = request.FILES['image']
                image_path = user_directory_paths(reply, image.name)
                with default_storage.open(image_path, 'wb+') as destination:
                    for chunk in image.chunks():
                        destination.write(chunk)
                # Resize ảnh nếu cần thiết
                with Image.open(default_storage.path(image_path)) as img:
                    img.thumbnail((300, 300))  # Adjust the size as needed
                    img.save(default_storage.path(image_path))
                reply.image = image_path
                reply.save()

            reply_created_on = naturaltime(current_time)
            ticket_url = reverse('ticket_details', kwargs={'ticket_id': ticket_id})
            
            # Thông báo cho người tạo bình luận gốc (nếu không phải là người reply)
            if reply.author != comment.author.user:
                message_to_comment_author = f'<a href="{ticket_url}" target="_blank">{reply.author.last_name} {reply.author.first_name} đã trả lời bình luận của bạn trong phiếu #{ticket.ticket_id}.'"<br>" f'<small>{reply_created_on}</small>'
                send_notification(comment.author.user.id, message_to_comment_author)
            
            # Thông báo cho người tạo ticket (nếu khác với người tạo bình luận và người reply)
            if reply.author != ticket.customer and comment.author.user != ticket.customer:
                message_to_creator = f'<a href="{ticket_url}" target="_blank">{reply.author.last_name} {reply.author.first_name} đã trả lời bình luận trong phiếu #{ticket.ticket_id} của bạn.'"<br>" f'<small>{reply_created_on}</small>'
                send_notification(ticket.customer.id, message_to_creator)
            
            # Thông báo cho kỹ thuật viên được giao (nếu có và khác với người reply và người tạo bình luận)
            if ticket.engineer and reply.author != ticket.engineer and comment.author.user != ticket.engineer:
                message_to_engineer = f'<a href="{ticket_url}" target="_blank">{reply.author.last_name} {reply.author.first_name} đã trả lời bình luận trong phiếu #{ticket.ticket_id} mà bạn đang xử lý.'"<br>" f'<small>{reply_created_on}</small>'
                send_notification(ticket.engineer.id, message_to_engineer)
            
            # Thông báo cho quản trị viên (trừ người reply nếu họ là admin)
            for superuser in superusers:
                if superuser != request.user:  # Không thông báo cho chính người reply
                    message_to_admin = f'<a href="{ticket_url}" target="_blank">{reply.author.last_name} {reply.author.first_name} đã trả lời bình luận trong phiếu #{ticket.ticket_id}.'"<br>" f'<small>{reply_created_on}</small>'
                    send_notification(superuser.id, message_to_admin)
            
            return redirect('ticket_details', ticket_id=ticket_id)

    return redirect('ticket_details', ticket_id=ticket_id)

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comments, id=comment_id)

    # Kiểm tra nếu người dùng hiện tại là tác giả của bình luận hoặc có quyền xóa
    if request.user == comment.user or request.user == comment.author.user:
        # Lặp qua tất cả các reply và xóa chúng
        for reply in comment.replies.all():
            reply.delete()

        # Cuối cùng, xóa bình luận
        comment.delete()

    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

@login_required
def delete_ticket(request, ticket_id):
    ticket = Ticket.objects.get(ticket_id=ticket_id)
    ticket.delete()
    delete_created_on = naturaltime(current_time)
    message = f'<a href="/" >Phiếu #{ticket.ticket_id} của bạn đã bị xóa bởi hệ thống.'"<br>" f'<small class="disable-text">{delete_created_on}</small></a>'
    send_notification(ticket.customer.id, message)
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

@login_required
def delete_ticket_details(request, ticket_id):
    ticket = Ticket.objects.get(ticket_id=ticket_id)
    ticket.delete()
    delete_created_on = naturaltime(current_time)
    message = f'<a href="/" >Phiếu #{ticket.ticket_id} của bạn đã bị xóa bởi hệ thống.'"<br>" f'<small class="disable-text">{delete_created_on}</small></a>'
    send_notification(ticket.customer.id, message)
    messages.success(request, f'Đã xóa phiếu {ticket.ticket_title}.')
    return redirect('admin_view_tickets')

@login_required
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, ticket_id=ticket_id)

    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('ticket_details', ticket_id=ticket_id)
    else:
        form = TicketForm(instance=ticket)

    return render(request, 'ticket_details.html', {'form': form, 'ticket': ticket})

@login_required
def change_assign_ticket_view(request, ticket_id):
    ticket = Ticket.objects.get(ticket_id=ticket_id)

    if request.method == 'POST':
        form = ChangeAssignTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            var = form.save(commit=False)
            var.is_assigned_to_engineer = True
            var.status = 'Đang xử lý'
            var.save()
            ticket_url = reverse('ticket_details', kwargs={'ticket_id': var.ticket_id})
            # Gửi thông báo đến người dùng mới
            new_engineer_id = var.engineer.id
            customer_id = var.customer.id
            change_assign_created_on = naturaltime(current_time)
            
            messages.success(request, f'Phiếu yêu cầu đã được đổi sang {var.engineer.last_name} {var.engineer.first_name} hỗ trợ')
            return redirect('admin_view_tickets')
        else:
            messages.warning(request, 'Đã có lỗi xảy ra, xin hãy thử lại.')
            return redirect('change_assign_ticket')
    else:
        form = ChangeAssignTicketForm(instance=ticket)
        form.fields['engineer'].queryset = User.objects.filter(is_engineer=True)
        context = {'form': form, 'ticket': ticket}
        return render(request, 'ticket/change_assign_ticket.html', context)
    
    
@login_required
def assign_ticket_view(request,ticket_id):
    ticket = Ticket.objects.get(ticket_id = ticket_id)
    if request.method == 'POST':
        form = AssignTicketForm(request.POST, instance=ticket)
        if form.is_valid():
            var = form.save(commit=False)
            var.is_assigned_to_engineer = True
            var.status = 'Đang xử lý'
            var.save()
            ticket_url = reverse('ticket_details', kwargs={'ticket_id': var.ticket_id})
            customer_id= var.customer.id
            engineer_id = var.engineer.id
            assign_created_on = naturaltime(current_time)
            message = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{var.ticket_id} của bạn đã được chuyển đến {var.engineer.last_name} {var.engineer.first_name}để hỗ trợ.'"<br>" f'<small>{assign_created_on}</small></a>'
            send_notification(customer_id, message)
            message1 = f'<a href="{ticket_url}" target="_blank">Phiếu yêu cầu #{var.ticket_id} đã được chuyển đến bạn để hỗ trợ.'"<br>" f'<small>{assign_created_on}</small></a>'
            send_notification(engineer_id, message1)
            messages.success(request, f'Phiếu yêu cầu đã được giao cho {var.engineer.last_name} {var.engineer.first_name}')
            return redirect('admin_view_tickets')
        else:
            messages.warning(request, 'Đã có lỗi xảy ra, xin hãy thử lại.')
            return redirect('assign_ticket') 
    else:
        form = AssignTicketForm(instance=ticket)
        form.fields['engineer'].queryset = User.objects.filter(is_engineer = True)
        context = {'form': form, 'ticket':ticket}
        return render(request, 'ticket/assign_ticket.html', context)
    
r = redis.from_url("redis://:iJuwEuyIQmk9jWX1gWqhnyzJYcwn6TFn@redis-14167.c89.us-east-1-3.ec2.redns.redis-cloud.com:14167/0")

def get_notifications(request):
    user_id = request.user.id

    # Lấy thông báo chưa đọc từ cơ sở dữ liệu
    notifications_db = Notification.objects.filter(user_id=user_id, read=False).order_by('-timestamp')
    
    # Lấy thông báo chưa đọc từ Redis nếu người dùng không online
    notifications_redis = []
    if not r.sismember("online_users", user_id):
        notifications_key = f"notifications_{user_id}"
        if r.exists(notifications_key):
            notifications_redis = [json.loads(notification) for notification in r.lrange(notifications_key, 0, -1)]
            # Xóa các thông báo đã lấy từ Redis để tránh lấy lại lần sau
            r.delete(notifications_key)
    
    # Ghép danh sách thông báo từ cả cơ sở dữ liệu và Redis
    notifications = list(notifications_db.values('message', 'timestamp'))
    notifications.extend(notifications_redis)

    return JsonResponse(notifications, safe=False)