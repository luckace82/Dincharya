from django import forms
from django.contrib.auth import get_user_model
from .models import Task

User = get_user_model()

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'assigned_to', 
            'priority', 'status', 'due_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'type': 'datetime-local'
                },
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter users to only show active users
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)
        
        # Set initial values
        if not self.instance.pk:  # Only for new tasks
            self.initial['status'] = 'todo'
            self.initial['priority'] = 'medium'

    def clean(self):
        cleaned_data = super().clean()
        assigned_to = cleaned_data.get('assigned_to')
        
        # If assigned_to has changed, set delegated_by to current user
        if assigned_to and assigned_to != getattr(self.instance, 'assigned_to', None):
            cleaned_data['delegated_by'] = self.user
            
        return cleaned_data
