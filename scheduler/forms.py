from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from .models import CustomUser

class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'role', 'groups', 'password1', 'password2']
