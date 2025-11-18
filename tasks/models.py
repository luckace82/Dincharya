from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_tasks',
        null=True
    )
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='assigned_tasks',
        null=True,
        blank=True
    )
    delegated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='delegated_tasks',
        null=True,
        blank=True
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='todo'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    # Approval workflow
    requires_approval = models.BooleanField(default=False)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Set created_by to the current user if not set
        is_create = not self.pk
        old = None
        if not self.pk and not self.created_by_id and hasattr(self, '_current_user'):
            self.created_by = self._current_user

        # If updating, load the old instance to detect changes for history
        if not is_create:
            try:
                old = Task.objects.get(pk=self.pk)
            except Task.DoesNotExist:
                old = None

        super().save(*args, **kwargs)

        # Create TaskHistory entries for important changes
        # TaskHistory is defined later in this module; reference directly
        try:
            TaskHistory
        except NameError:
            TaskHistory = None

        if TaskHistory:
            # On create
            if is_create:
                TaskHistory.objects.create(
                    task=self,
                    actor=getattr(self, '_current_user', None),
                    action='created',
                    old_value='',
                    new_value=self.title
                )
            else:
                # Status change
                if old and old.status != self.status:
                    TaskHistory.objects.create(
                        task=self,
                        actor=getattr(self, '_current_user', None),
                        action='status_changed',
                        old_value=old.status,
                        new_value=self.status
                    )
                # Assignment change
                old_assignee = old.assigned_to_id if old else None
                if old_assignee != (self.assigned_to_id if self.assigned_to_id else None):
                    TaskHistory.objects.create(
                        task=self,
                        actor=getattr(self, '_current_user', None),
                        action='assigned_changed',
                        old_value=str(old_assignee),
                        new_value=str(self.assigned_to_id)
                    )
                # Approval change
                old_approved = getattr(old, 'approved', False)
                if old_approved != self.approved:
                    TaskHistory.objects.create(
                        task=self,
                        actor=getattr(self, '_current_user', None),
                        action='approval_changed',
                        old_value=str(old_approved),
                        new_value=str(self.approved)
                    )

    class Meta:
        ordering = ['-created_at']


class TaskHistory(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('status_changed', 'Status Changed'),
        ('assigned_changed', 'Assigned Changed'),
        ('approval_changed', 'Approval Changed'),
        ('deleted', 'Deleted'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='history')
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task_id} - {self.action} @ {self.timestamp}"
