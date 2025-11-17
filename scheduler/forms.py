from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from .models import CustomUser

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
