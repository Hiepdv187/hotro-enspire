from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ticket.models import Ticket
from todo.models import TodoList, TaskList
@login_required
def dashboard(request):
    if request.user.is_customer:
        tickets = Ticket.objects.filter(customer=request.user).count()
        active_tickets = Ticket.objects.filter(customer=request.user, is_resolved=False).count
        closed_tickets = Ticket.objects.filter(customer=request.user, is_resolved=True).count
        context = {
            'tickets': tickets, 'active_tickets':active_tickets,
            'closed_tickets': closed_tickets
            }
        return render(request, 'dashboard/customer_dashboard.html', context)
    elif request.user.is_engineer:
        tickets = Ticket.objects.filter(engineer=request.user).count()
        active_tickets = Ticket.objects.filter(engineer=request.user, is_resolved=False).count
        closed_tickets = Ticket.objects.filter(engineer=request.user, is_resolved=True).count
        context = {
            'tickets': tickets, 'active_tickets':active_tickets,
            'closed_tickets': closed_tickets
            }
        return render(request, 'dashboard/engineer_dashboard.html', context)
    elif request.user.is_superuser:
        tickets_count = Ticket.objects.all().count()
        active_tickets_count = Ticket.objects.filter(is_resolved=False).count()
        closed_tickets_count = Ticket.objects.filter(is_resolved=True).count()
        context = {
            'tickets_count': tickets_count,
            'active_tickets_count': active_tickets_count,
            'closed_tickets_count': closed_tickets_count
        }
        return render(request, 'dashboard/admin_dashboard.html', context)
    
@login_required
def todo_dashboard(request):
    todo_lists=TodoList.objects.filter(user=request.user).count()
    active_todo_list= TodoList.objects.filter(user=request.user, todo_list_is_resolved=False).count
    closed_todo_list = TodoList.objects.filter(user=request.user, todo_list_is_resolved=True).count
    context = {
        'todo_lists': todo_lists, 'active_todo_list':active_todo_list,
        'closed_todo_list': closed_todo_list
        }
    return render(request, 'dashboard/todo_dashboard.html', context)
