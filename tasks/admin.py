from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Task

User = get_user_model()

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'assigned_to', 'priority', 'status', 'due_date', 'created_at')
    list_filter = ('priority', 'status', 'created_at')
    search_fields = ('title', 'description', 'created_by__username', 'assigned_to__username')
    readonly_fields = ('created_by', 'delegated_by', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
