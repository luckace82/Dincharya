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
    """
    Sign up view for new interns.
    Supervisors are created through the admin panel only.
    """
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()  # Role is set to 'intern' in form.save()
            return redirect('login')
    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})
