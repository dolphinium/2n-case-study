from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Personnel Authentication
    path('login/personnel/', views.personnel_login, name='personnel_login'),
    path('logout/personnel/', auth_views.LogoutView.as_view(next_page='personnel_login'), name='personnel_logout'),

    # Authorized User Authentication
    path('login/authorized/', views.authorized_login, name='authorized_login'),
    path('logout/authorized/', auth_views.LogoutView.as_view(next_page='authorized_login'), name='authorized_logout'),
    
    # Dashboard URLs
    path('dashboard/personnel/', views.personnel_dashboard, name='personnel_dashboard'),
    path('dashboard/authorized/', views.authorized_dashboard, name='authorized_dashboard'),
    
    # Attendance URLs
    path('attendance/check-in/', views.attendance_check_in, name='attendance_check_in'),
    path('attendance/check-out/', views.attendance_check_out, name='attendance_check_out'),
    
    # Attendance Reporting
    path('attendance/records/', views.view_attendance_records, name='view_attendance_records'),
    
    # Leave Management URLs
    path('leave/balance/', views.view_leave_balance, name='view_leave_balance'),
    path('leave/request/', views.request_leave, name='request_leave'),
    path('leave/pending/', views.view_pending_leave_requests, name='view_pending_leave_requests'),
    path('leave/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
]