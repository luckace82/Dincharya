from django.contrib.auth.decorators import login_required
from django.shortcuts import render , redirect
from .decorators import supervisor_required
from django.http import HttpResponseForbidden
from .models import CustomUser
from .forms import SignUpForm
from django.contrib.auth.models import Group


@login_required
def dashboard(request):
    from tasks.models import Task
    
    user = request.user
    # Get the latest 5 tasks for the current user, ordered by due date
    from django.utils import timezone
    user_tasks = Task.objects.filter(assigned_to=user).order_by('due_date')[:5]
    # Counts for the stats section
    user_all_tasks_qs = Task.objects.filter(assigned_to=user)
    tasks_assigned_count = user_all_tasks_qs.count()
    tasks_completed_count = user_all_tasks_qs.filter(status='completed').count()
    tasks_inprogress_count = user_all_tasks_qs.filter(status='in_progress').count()

    context = {
        'user': user,
        'recent_tasks': user_tasks,
        'now': timezone.now(),
        'tasks_assigned_count': tasks_assigned_count,
        'tasks_completed_count': tasks_completed_count,
        'tasks_inprogress_count': tasks_inprogress_count,
    }
    
    if user.role == 'supervisor':
        return render(request, 'supervisor_dashboard.html', context)
    elif user.role == 'intern':
        return render(request, 'intern_dashboard.html', context)
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
