from django.contrib.auth.decorators import login_required
from django.shortcuts import render , redirect, get_object_or_404
from .decorators import supervisor_required
from django.http import HttpResponseForbidden
from .models import CustomUser
from .forms import SignUpForm
from .forms import SupportTicketForm
from .models import SupportTicket
from .forms import SupportReplyForm
from .models import SupportReply
from django.core.mail import send_mail
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
from django.contrib.auth.models import Group
import csv
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
from django.db.models.functions import TruncWeek
from django.utils import timezone
from tasks.models import Task
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.views import View
from django.contrib import messages
from .forms import BulkReassignForm


@login_required
def dashboard(request):
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
        interns = CustomUser.objects.filter(role='intern')
        team_tasks = Task.objects.filter(assigned_to__in=interns)

        summary = interns.annotate(
            assigned_count=Count('assigned_tasks'),
            completed_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed')),
            inprogress_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='in_progress')),
            overdue_count=Count('assigned_tasks', filter=Q(assigned_tasks__due_date__lt=timezone.now()))
        )
        context.update({
            'team_summary': summary,
            'team_overview': {
                'total': team_tasks.count(),
                'completed': team_tasks.filter(status='completed').count(),
                'in_progress': team_tasks.filter(status='in_progress').count(),
                'overdue': team_tasks.filter(due_date__lt=timezone.now()).count(),
            }
        })
        # Supervisor-level aggregates
        interns_count = interns.count()
        from django.contrib.auth.models import Group
        groups_count = Group.objects.count()
        total_tasks = team_tasks.count()
        completed = team_tasks.filter(status='completed').count()
        completion_rate = round((completed / total_tasks) * 100, 1) if total_tasks else 0

        context.update({
            'interns_count': interns_count,
            'groups_count': groups_count,
            'completion_rate': completion_rate,
        })
        # Recent support tickets for supervisors
        recent_tickets = SupportTicket.objects.filter(status__in=['open', 'in_progress']).select_related('created_by')[:5]
        open_tickets_count = SupportTicket.objects.filter(status='open').count()
        context.update({
            'recent_tickets': recent_tickets,
            'open_tickets_count': open_tickets_count,
        })
        return render(request, 'supervisor_dashboard.html', context)
    elif user.role == 'intern':
        # Provide intern's own tickets to their dashboard
        my_tickets = SupportTicket.objects.filter(created_by=user).select_related('assigned_to').prefetch_related('replies__responder')[:5]
        context.update({
            'my_tickets': my_tickets,
        })
        return render(request, 'intern_dashboard.html', context)
    else:
        return render(request, 'unauthorized.html')


@login_required
@supervisor_required
def export_team_summary_csv(request):
    """Export a CSV with per-intern task summary."""
    interns = CustomUser.objects.filter(role='intern')
    summary = interns.annotate(
        assigned_count=Count('assigned_tasks'),
        completed_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='completed')),
        inprogress_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='in_progress')),
        overdue_count=Count('assigned_tasks', filter=Q(assigned_tasks__due_date__lt=timezone.now()))
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="team_summary.csv"'

    writer = csv.writer(response)
    writer.writerow(['Intern ID', 'Username', 'Name', 'Assigned', 'In Progress', 'Completed', 'Overdue', 'Completion %'])

    for intern in summary:
        total = intern.assigned_count or 0
        completed = intern.completed_count or 0
        completion_pct = round((completed / total) * 100, 1) if total else 0
        # get_full_name may not exist on custom user; guard
        name = getattr(intern, 'get_full_name', None)
        if callable(name):
            display_name = intern.get_full_name() or intern.username
        else:
            display_name = getattr(intern, 'first_name', '') or intern.username

        writer.writerow([
            intern.id,
            intern.username,
            display_name,
            total,
            intern.inprogress_count or 0,
            completed,
            intern.overdue_count or 0,
            completion_pct,
        ])

    return response


@login_required
@supervisor_required
def tasks_time_series(request):
    """Return JSON series for tasks created and completed per week (last 12 weeks)."""
    end = timezone.now()
    start = end - timezone.timedelta(weeks=12)

    created_qs = Task.objects.filter(created_at__gte=start)
    created = created_qs.annotate(week=TruncWeek('created_at')).values('week').annotate(count=Count('id')).order_by('week')

    completed_qs = Task.objects.filter(updated_at__gte=start, status='completed')
    completed = completed_qs.annotate(week=TruncWeek('updated_at')).values('week').annotate(count=Count('id')).order_by('week')

    data = {}
    for row in created:
        key = row['week'].date().isoformat()
        data.setdefault(key, {})['created'] = row['count']
    for row in completed:
        key = row['week'].date().isoformat()
        data.setdefault(key, {})['completed'] = row['count']

    # ensure all weeks present
    series = []
    # Build list of weeks between start and end by week start
    cur = start - timezone.timedelta(days=start.weekday())
    while cur <= end:
        key = cur.date().isoformat()
        vals = data.get(key, {})
        series.append({'week': key, 'created': vals.get('created', 0), 'completed': vals.get('completed', 0)})
        cur = cur + timezone.timedelta(weeks=1)

    return JsonResponse(series, safe=False)



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


class SupervisorOrOwnerMixin:
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object() if hasattr(self, 'get_object') else None
        if request.user.role == 'supervisor':
            return super().dispatch(request, *args, **kwargs)
        # Fallback: owner/assignee only
        if obj and (obj.created_by == request.user or obj.assigned_to == request.user):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class TaskUpdateView(LoginRequiredMixin, SupervisorOrOwnerMixin, UpdateView):
    ...


class BulkReassignView(LoginRequiredMixin, View):
    def get(self, request):
        form = BulkReassignForm(user=request.user)
        return render(request, 'tasks/bulk_reassign.html', {'form': form})
    def post(self, request):
        form = BulkReassignForm(request.POST)
        if form.is_valid():
            task_ids = form.cleaned_data['task_ids']  # list of ids
            new_user = form.cleaned_data['assigned_to']
            # Iterate and save each task so history and save logic run
            qs = Task.objects.filter(id__in=[t.id for t in task_ids])
            for task in qs:
                task.assigned_to = new_user
                task.delegated_by = request.user
                task._current_user = request.user
                task.save()
            messages.success(request, 'Tasks reassigned.')
            return redirect('tasks:task_list')
        return render(request, 'tasks/bulk_reassign.html', {'form': form})


@login_required
@supervisor_required
def approve_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.approved = True
    task.current_user = request.user
    task.save()
    messages.success(request, 'Task approved.')
    return redirect('tasks:task_list')


@login_required
@supervisor_required
def reports_page(request):
    """Render the reports page which contains CSV export and the full chart.
    The chart data is fetched from the existing `tasks_time_series` JSON endpoint.
    """
    # Minimal context; the template will fetch timeseries data and call export URL
    return render(request, 'reports.html', {})


@login_required
def support_ticket_create(request):
    """Allow interns (and supervisors) to create support tickets."""
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            messages.success(request, 'Support ticket submitted. Your supervisor will be notified.')
            return redirect('dashboard')
    else:
        form = SupportTicketForm()
    return render(request, 'support/create_ticket.html', {'form': form})


@login_required
@supervisor_required
def support_ticket_list(request):
    """Supervisor view: list recent tickets."""
    tickets = SupportTicket.objects.all().select_related('created_by', 'assigned_to')[:50]
    return render(request, 'support/ticket_list.html', {'tickets': tickets})


@login_required
def support_ticket_detail(request, pk):
    """View a ticket. Supervisors can post replies; ticket owners (interns) can view the ticket and replies.
    Posting is restricted to supervisors to keep replies authoritative.
    """
    ticket = get_object_or_404(SupportTicket, pk=pk)

    # Permission: allow if supervisor or ticket owner
    is_supervisor = request.user.is_superuser or getattr(request.user, 'role', None) == 'supervisor'
    if not (is_supervisor or ticket.created_by == request.user):
        return HttpResponseForbidden("You don't have permission to view this ticket.")

    # Load replies defensively
    try:
        replies = list(ticket.replies.select_related('responder').all())
    except Exception as exc:
        logger.exception('Failed to load replies for ticket %s', pk)
        messages.error(request, 'Failed to load ticket replies (see server logs).')
        replies = []

    # Only supervisors may POST replies
    if request.method == 'POST':
        if not is_supervisor:
            return HttpResponseForbidden("Only supervisors can post replies.")
        form = SupportReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.ticket = ticket
            reply.responder = request.user
            reply.save()

            # Send email notification to ticket owner if they have an email
            recipient_email = getattr(ticket.created_by, 'email', None)
            if recipient_email:
                subject = f"Response to your support ticket #{ticket.id}: {ticket.subject}"
                body = (
                    f"Hello {ticket.created_by.get_full_name() or ticket.created_by.username},\n\n"
                    f"A supervisor has replied to your support ticket:\n\n{reply.message}\n\n"
                    "--\nDincharya Support Team"
                )
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
                try:
                    send_mail(subject, body, from_email, [recipient_email], fail_silently=True)
                except Exception:
                    logger.exception('Failed to send support reply email for ticket %s', ticket.pk)

            # Analyze reply to determine if a concrete solution was provided.
            # If a solution keyword is present, mark ticket as resolved so it
            # moves out of the open queue. Otherwise, set a follow-up flag and
            # generate a short follow-up note so supervisors can easily see it.
            msg_text = (reply.message or '').lower()
            solution_keywords = ['fix', 'fixed', 'resolve', 'resolved', 'solution', 'patched', 'workaround', 'done', 'implemented', 'completed']
            provided_solution = any(k in msg_text for k in solution_keywords)

            if provided_solution:
                ticket.status = 'resolved'
                ticket.follow_up_required = False
                ticket.follow_up_note = ''
            else:
                ticket.follow_up_required = True
                # Generate a concise follow-up note highlighting potential effects
                ticket.follow_up_note = (
                    "No clear solution provided in supervisor reply. Potential effects:\n"
                    "1) Blocked intern progress\n"
                    "2) Incorrect or incomplete results\n"
                    "3) Possible data inconsistency or loss depending on context\n\n"
                    "Please follow up with a proposed remediation or mark the ticket as resolved when fixed."
                )

            # Update ticket timestamp and save
            ticket.updated_at = timezone.now()
            ticket.save()

            messages.success(request, 'Reply posted and intern notified.')
            return redirect('support_detail', pk=ticket.pk)
    else:
        # Show empty form only to supervisors
        form = SupportReplyForm() if is_supervisor else None

    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'replies': replies,
        'form': form,
        'is_supervisor': is_supervisor,
    })
