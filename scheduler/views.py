from django.contrib.auth.decorators import login_required
from django.shortcuts import render , redirect
from .decorators import supervisor_required
from django.http import HttpResponseForbidden
from .models import CustomUser
from .forms import SignUpForm
from django.contrib.auth.models import Group


@login_required
def dashboard(request):
    user = request.user
    if user.role == 'supervisor':
        return render(request, 'supervisor_dashboard.html', {'user': user})
    elif user.role == 'intern':
        return render(request, 'intern_dashboard.html', {'user': user})
    else:
        return render(request, 'unauthorized.html')



@supervisor_required
def manage_interns(request):
    if request.user.role != 'supervisor':
        return HttpResponseForbidden("Only supervisors can view this page.")
    
    interns = CustomUser.objects.filter(role='intern')
    return render(request, 'manage_interns.html', {'interns': interns})


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            if user.role == 'intern':
                selected_groups = form.cleaned_data.get('groups')
                for group in selected_groups:
                    user.groups.add(group)

            return redirect('login')
    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})
