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
