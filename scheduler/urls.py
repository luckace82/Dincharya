from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.dashboard, name='dashboard'),
    path('signup/', views.signup_view, name='signup'),
    path('manage-interns/', views.manage_interns, name='manage_interns'),
    path('tasks/bulk-reassign/', views.BulkReassignView.as_view(), name='bulk_reassign'),
    path('tasks/<int:pk>/approve/', views.approve_task, name='approve_task'),
    path('reports/team-summary/', views.export_team_summary_csv, name='export_team_summary'),
    path('reports/tasks-timeseries/', views.tasks_time_series, name='tasks_time_series'),
    path('reports/', views.reports_page, name='reports'),
    path('support/new/', views.support_ticket_create, name='support_create'),
    path('support/', views.support_ticket_list, name='support_list'),
    path('support/<int:pk>/', views.support_ticket_detail, name='support_detail'),
]
