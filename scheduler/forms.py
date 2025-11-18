from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from .models import CustomUser
from .models import SupportTicket

from django.contrib.auth import get_user_model
from tasks.models import Task

User = get_user_model()


class BulkReassignForm(forms.Form):
    task_ids = forms.ModelMultipleChoiceField(
        queryset=Task.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label='Select Tasks to Reassign'
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=True,
        label='Assign to'
    )

    def __init__(self, *args, **kwargs):
        # allow passing user for context or permission-based filtering later
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

class SignUpForm(UserCreationForm):
    """
    Sign up form for interns only.
    Supervisors can only be created through the admin panel.
    """
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Department/Group (Optional)"
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'groups', 'password1', 'password2']
    
    def save(self, commit=True):
        """Override save to set role as 'intern' automatically"""
        user = super().save(commit=False)
        user.role = 'intern'  # Force role to intern
        if commit:
            user.save()
            # Add selected groups
            selected_groups = self.cleaned_data.get('groups')
            if selected_groups:
                for group in selected_groups:
                    user.groups.add(group)
        return user


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ['subject', 'description', 'priority']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Short description of the issue'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe the issue and steps to reproduce'}),
            'priority': forms.Select(attrs={'class': 'form-select'})
        }
