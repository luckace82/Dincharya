from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Task, TaskHistory

User = get_user_model()

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'assigned_to', 'priority', 'status', 'due_date', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    list_display = ('title', 'created_by', 'assigned_to', 'priority', 'status', 'approved', 'due_date', 'created_at')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')
    readonly_fields = ('created_by', 'delegated_by', 'created_at', 'updated_at')
    # Allow admins to approve tasks from admin UI if needed
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('task', 'action', 'actor', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('task__title', 'actor__username')
