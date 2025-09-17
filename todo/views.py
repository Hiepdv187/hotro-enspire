from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import uuid
import json
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .form import CreateTodoListForm, CreateTaskListForm, EditTaskForm
import random
import string
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views import View
from django.http import JsonResponse,Http404
import uuid
from django.db.models import Q
from uuid import UUID
from .models  import TodoList, TaskList
from django.urls import reverse
@login_required
def create_todo_list(request):
    if request.method == 'POST':
        form = CreateTodoListForm(request.POST)
        if form.is_valid():
            todo_list = form.save(commit=False)
            todo_list.user = request.user
            todo_list.todo_list_id = str(uuid.uuid4())[:8] 
            todo_list.save()
            messages.success(request, 'Đã tạo thành công.')
            return redirect('active_todo_list')
        else:
            print(form.errors)
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng nhập lại')
            return redirect('create_todo_list')
    else:
        form = CreateTodoListForm()
    context = {'form': form}
    return render(request, 'todo/create_todo_list.html', context)
    

@login_required
def todo_list_details(request, todo_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    task_lists = TaskList.objects.filter(todo_list=todo_list)
    edit_mode = 'edit' in request.GET
    if edit_mode:
        # Xử lý chế độ chỉnh sửa
        if request.method == 'POST':
            task_list_form = CreateTaskListForm(request.POST)
            if task_list_form.is_valid():
                # Cập nhật task_list theo todo_list
                task_list = task_list_form.save(commit=False)
                task_list.todo_list = todo_list
                task_list.save()
                return redirect('todo_list_details', todo_list_id=todo_list_id)
        else:
            # Hiển thị form chỉnh sửa
            task_list_form = CreateTaskListForm()

        task_lists = TaskList.objects.filter(todo_list=todo_list)

        return render(request, 'todo/todo_list_details.html', {'todo_list': todo_list, 'task_list_form': task_list_form, 'task_lists': task_lists, 'edit_mode': edit_mode})
    
    if request.method == 'POST':
        task_list_form = CreateTaskListForm(request.POST)
        if task_list_form.is_valid():
            task_list = task_list_form.save(commit=False)
            task_list.todo_list = todo_list
            task_list.user = request.user
            task_list.save()

            messages.success(request, 'Đã thêm task mới.')
            return redirect('todo_list_details', todo_list_id=todo_list_id)
        

    else:
        task_list_form = CreateTaskListForm()

    task_lists = TaskList.objects.filter(todo_list=todo_list)
    all_task_lists_resolved = todo_list.tasks.filter(task_list_is_resolved=False).count() == 0
    context = {'todo_list': todo_list, 'task_list_form': task_list_form, 'task_lists': task_lists, 'all_task_lists_resolved': all_task_lists_resolved}
    return render(request, 'todo/todo_list_details.html', {'todo_list': todo_list, 'task_lists': task_lists, 'edit_mode': edit_mode, 'all_task_lists_resolved': all_task_lists_resolved})


@login_required
def active_todo_list(request):
    todo_lists = TodoList.objects.filter(user=request.user, todo_list_is_resolved = False).order_by('-todo_list_create_time')
    context = {'todo_lists': todo_lists}
    return render(request, 'todo/active_todo_list.html', context)

@login_required
def resolved_todo_list(request):
    todo_lists = TodoList.objects.filter(user=request.user, todo_list_is_resolved = True).order_by('-todo_list_create_time')
    context = {'todo_lists': todo_lists}
    return render(request, 'todo/resolved_todo_list.html', context)

@login_required
def view_todo_list(request):
    todo_lists = TodoList.objects.filter(user=request.user).order_by('-todo_list_create_time')
    context = {'todo_lists': todo_lists}
    return render(request, 'todo/view_todo_list.html', context)


@login_required
def edit_task_list(request, todo_list_id, task_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    task_list = get_object_or_404(TaskList, id=task_list_id, todo_list=todo_list)

    if request.method == 'POST':
        task_list_form = EditTaskForm(request.POST, instance=task_list)
        if task_list_form.is_valid():
            task_list_form.save()
            messages.success(request, 'Đã cập nhật task thành công.')
            return redirect('todo_list_details', todo_list_id=todo_list_id)
        else:
            messages.warning(request, 'Đã xảy ra lỗi, xin vui lòng nhập lại')
    else:
        task_list_form = EditTaskForm(instance=task_list)

    context = {'todo_list': todo_list, 'task_list_form': task_list_form, 'task_list': task_list}
    return render(request, 'todo/todo_list_details.html', context)

@login_required
def delete_task_list(request, todo_list_id, task_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    task_list = get_object_or_404(TaskList, id=task_list_id, todo_list=todo_list)

    if request.method == 'POST':
        task_list.delete()
        messages.success(request, 'Đã xóa task thành công.')
    return redirect('todo_list_details', todo_list_id=todo_list_id)


@login_required
def delete_todo_list(request, todo_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    todo_list.delete()
    messages.success(request, f'Đã xóa công việc {todo_list.todo_list_title}.')
    return redirect(request.META.get('HTTP_REFERER', 'fallback-url'))

@method_decorator(csrf_exempt, name='dispatch')
class AddTaskView(View):
    def post(self, request, *args, **kwargs):
        try:
            # Lấy dữ liệu từ request.POST hoặc request.body
            data = json.loads(request.body)

            
            task_content = data.get('task_list_description', '')

            
            new_task = {'task_list_description': task_content, 'other_field': 'Giá trị khác'}
            return JsonResponse(new_task, status=200)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@csrf_exempt
@login_required
def update_task_status(request, todo_list_id, task_list_id):
    print(f"Received todo_list_id: {todo_list_id}, task_list_id: {task_list_id}")

    try:
        todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id, user=request.user)
        # Update the filter to use 'id' instead of 'task_list_id'
        task_list = get_object_or_404(TaskList, id=task_list_id, todo_list=todo_list)
    except Http404 as e:
        return JsonResponse({'status': 'error', 'message': str(e), 'task_list_id': task_list_id})

    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        task_status = data.get('task_status')

        if task_status == 'resolved':
            task_list.task_list_is_resolved = True
            task_list.task_list_is_unresolved = False
        elif task_status == 'unresolved':
            task_list.task_list_is_resolved = False
            task_list.task_list_is_unresolved = True

        task_list.save()
        return JsonResponse({'status': 'success', 'task_list_id': task_list_id})

    return JsonResponse({'status': 'error', 'message': 'Invalid request', 'task_list_id': task_list_id})

@login_required
def resolve_todo_list(request, todo_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    if request.method == 'POST':
        todo_list.todo_list_is_resolved = True
        todo_list.todo_list_status = 'Đã xong'
        todo_list.save()
        messages.success(request, f'Công việc {todo_list.todo_list_title} đã được hoàn thành!')

    return redirect('active_todo_list')

@login_required
def delete_todo_list_details(request, todo_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    todo_list.delete()
    messages.success(request, f'Đã xóa công việc {todo_list.todo_list_title}.')
    return redirect('view_todo_list')

@login_required
def delete_todo_list_resolved(request, todo_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    todo_list.delete()
    messages.success(request, f'Đã xóa công việc {todo_list.todo_list_title}.')
    return redirect('resolved_todo_list')

@login_required
def search_todo_list(request):
    query = request.GET.get('query', '')
    todo_lists = None
    task_lists = None

    if query.isdigit():
        # If query is a digit, search for TaskList
        task_lists = TaskList.objects.filter(todo_list__todo_list_title__icontains=query)
        todo_lists = TodoList.objects.filter(tasks__in=task_lists)
        

    else:
        # Search for TodoList objects where the title or status contains the query
        todo_lists = TodoList.objects.filter(
            Q(todo_list_title__icontains=query) |
            Q(todo_list_status__icontains=query),
            user=request.user
        )
        
        # Initialize task_lists as an empty queryset
        task_lists = TaskList.objects.none()

    context = {
        'query': query,
        'task_lists': task_lists,
        'todo_lists': todo_lists,
    }

    return render(request, 'todo/search_todo_list.html', context)
@login_required
def delete_todo_list_search(request, todo_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    todo_list.delete()
    messages.success(request, 'Đã xóa thành công')
    return redirect('search_todo_list')

@login_required
def edit_todo_list(request, todo_list_id):
    todo_list = get_object_or_404(TodoList, todo_list_id=todo_list_id)
    
    if request.method == 'POST':
        form = CreateTodoListForm(request.POST, instance=todo_list)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật thành công')
            return redirect('active_todo_list')
    else:
        form = CreateTodoListForm(instance=todo_list)
    
    return redirect('active_todo_list')