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

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Set created_by to the current user if not set
        if not self.pk and not self.created_by_id and hasattr(self, '_current_user'):
            self.created_by = self._current_user
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
