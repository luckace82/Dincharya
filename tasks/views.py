from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import Task
from .forms import TaskForm

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 10
    
    

    def get_queryset(self):
        # Allow supervisors/superusers to filter by a specific assigned user via GET param
        assigned_user = self.request.GET.get('assigned_to')
        role = getattr(self.request.user, 'role', None)
        

        queryset = None
        if assigned_user and (self.request.user.is_superuser or role == 'supervisor'):
            try:
                assigned_id = int(assigned_user)
                queryset = Task.objects.filter(assigned_to__id=assigned_id)
            except (ValueError, TypeError):
                queryset = Task.objects.none()

        # If no explicit assigned filter, decide default scope
        if queryset is None:
            # If the user requested only their assigned tasks
            if 'assigned_to_me' in self.request.GET:
                queryset = Task.objects.filter(assigned_to=self.request.user)
            else:
                # Superusers see all tasks by default, supervisors and interns see their assigned tasks
                if self.request.user.is_superuser:
                    queryset = Task.objects.all()
                else:
                    queryset = Task.objects.filter(assigned_to=self.request.user)

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Order by due date then priority
        queryset = queryset.order_by('due_date', '-priority')

        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Task.STATUS_CHOICES
        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance._current_user = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Task created successfully!')
        return response

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('tasks:task_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        old_assigned_to = self.get_object().assigned_to
        response = super().form_valid(form)
        
        # Check if assigned_to has changed
        if old_assigned_to != form.instance.assigned_to and form.instance.assigned_to:
            form.instance.delegated_by = self.request.user
            form.instance.save()
            
        messages.success(self.request, 'Task updated successfully!')
        return response

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('tasks:task_list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, 'Task deleted successfully!')
        return response

@login_required
def update_task_status(request, pk, status):
    task = get_object_or_404(Task, pk=pk)
    
    # Verify user has permission to update this task
    if task.assigned_to != request.user and task.created_by != request.user:
        messages.error(request, "You don't have permission to update this task.")
        return redirect('tasks:task_list')
    
    # Update status
    task.status = status
    task.updated_at = timezone.now()
    task.save()
    
    messages.success(request, f'Task marked as {dict(Task.STATUS_CHOICES).get(status, status)}')
    return redirect('tasks:task_list')
