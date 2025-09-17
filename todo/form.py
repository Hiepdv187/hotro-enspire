from django import forms
from .models import TodoList, TaskList
from accounts.models import User

class CreateTodoListForm(forms.ModelForm):
    class Meta:
        model = TodoList
        fields = ['todo_list_title']
        

class TodoListForm(forms.ModelForm):
    class Meta:
        model = TodoList
        fields = ['todo_list_title']

class TaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ['task_list_description', 'task_list_is_resolved', 'task_list_is_unresolved']
        widgets = {
            'task_list_description': forms.Textarea(attrs={'rows': 1}),
            'task_list_is_resolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'task_list_is_unresolved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        
class CreateTaskListForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ['task_list_description']
        widgets = {
            'task_list_description': forms.Textarea(attrs={'rows': 1}),
        }

class EditTaskForm(forms.ModelForm):
    class Meta:
        model = TaskList
        fields = ['task_list_description']