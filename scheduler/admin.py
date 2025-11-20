from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


class CustomUserAdmin(BaseUserAdmin):
    """
    Custom admin interface for CustomUser model.
    Allows creation of supervisors through admin panel only.
    """
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    
    # Fields to display in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    # Add role field in the add user form
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Selection', {
            'fields': ('role',),
            'description': 'Select "supervisor" to create a supervisor account. Regular users should select "intern".'
        }),
    )


admin.site.register(CustomUser, CustomUserAdmin)

from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'created_by', 'assigned_to', 'priority', 'status', 'follow_up_required', 'created_at')
    list_filter = ('status', 'priority', 'created_at', 'follow_up_required')
    search_fields = ('subject', 'description', 'created_by__username')
    ordering = ('-created_at',)
    readonly_fields = ('follow_up_note',)


from .models import SupportReply


@admin.register(SupportReply)
class SupportReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'responder', 'created_at')
    search_fields = ('ticket__subject', 'responder__username', 'message')
