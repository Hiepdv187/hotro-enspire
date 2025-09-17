from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.conf import settings
class TodoList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    todo_list_id = models.CharField(max_length=20, unique=True)
    todo_list_title = models.CharField(max_length=300, blank = True, null = True, default = '')
    todo_list_status = models.CharField(max_length=50, choices=(('Đang làm','Đang làm'), ('Đã xong', 'Đã xong')), default = 'Đang làm')
    todo_list_create_time = models.DateTimeField(auto_now_add=True)
    todo_list_is_resolved = models.BooleanField(default = False)
    def __str__(self):
        return self.todo_list_title
class TaskList(models.Model):
    todo_list = models.ForeignKey(TodoList, on_delete=models.CASCADE, null=True, related_name='tasks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    task_list_description=models.CharField(max_length=500, blank = False, null = False, default = '')
    task_list_is_resolved = models.BooleanField(default = False)
    task_list_is_unresolved = models.BooleanField(default = False)
    def __str__(self):
        return self.task_list_description