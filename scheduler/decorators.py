from django.http import HttpResponseForbidden

def supervisor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.role != 'supervisor':
            return HttpResponseForbidden("Only supervisors can access this page.")
        return view_func(request, *args, **kwargs)
    return wrapper
