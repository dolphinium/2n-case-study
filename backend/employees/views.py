from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .decorators import personnel_required, authorized_user_required    # custom decorators
from .forms import CheckInForm, CheckOutForm
from .models import AttendanceRecord, LeaveRequest, Notification, MonthlyReport, User
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import Q, Sum
from django.db import models
from django.core.paginator import Paginator
from decimal import Decimal
from .forms import LeaveRequestForm
from django.shortcuts import get_object_or_404

def personnel_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and not user.is_authorized:
            login(request, user)
            return redirect('personnel_dashboard')  # Define this URL later
        else:
            messages.error(request, 'Invalid Credentials or Unauthorized Access.')
    return render(request, 'employees/personnel_login.html')

def authorized_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_authorized:
            login(request, user)
            return redirect('authorized_dashboard')  # Define this URL later
        else:
            messages.error(request, 'Invalid Credentials or Unauthorized Access.')
    return render(request, 'employees/authorized_login.html')


def is_personnel(user):
    return user.is_authenticated and not user.is_authorized

def is_authorized_user(user):
    return user.is_authenticated and user.is_authorized

@personnel_required
def personnel_dashboard(request):
    return render(request, 'employees/personnel_dashboard.html')

@authorized_user_required
def authorized_dashboard(request):
    notifications = request.user.notifications.filter(is_read = False).order_by('-timestamp')
    # set up this mechanism later
    # notifications.update(is_read=True)    
    return render(request, 'employees/authorized_dashboard.html', {'notifications': notifications})

@login_required(login_url='personnel_login')
@user_passes_test(is_personnel)
def attendance_check_in(request):
    user = request.user
    today = timezone.now().date()
    now_time = timezone.now().time()

    attendance, created = AttendanceRecord.objects.get_or_create(employee=user, date=today)

    if attendance.first_check_in:
        messages.info(request, "You have already checked in today.")
        return redirect('personnel_dashboard')

    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            check_in_time = form.cleaned_data.get('check_in_time') or now_time
            attendance.first_check_in = check_in_time

            # Determine if late
            company_start_time = time(8, 0)  # 08:00 AM
            if check_in_time > company_start_time:
                attendance.is_late = True
                # Calculate lateness_duration
                check_in_datetime = datetime.combine(today, check_in_time)
                company_start_datetime = datetime.combine(today, company_start_time)
                lateness = check_in_datetime - company_start_datetime
                attendance.lateness_duration = lateness

                # Calculate leave deduction
                lateness_minutes = lateness.seconds // 60
                deduction_rate = 0.25  # 0.25 days per 30 minutes
                deduction = (lateness_minutes / 30) * deduction_rate
                deduction = round(Decimal(deduction), 2)

                # Update leave balance
                profile = user.profile  # Assuming OneToOneField from User to EmployeeProfile
                if profile.annual_leave_balance >= deduction:
                    profile.annual_leave_balance -= deduction
                    profile.save()
                    attendance.leave_deducted = deduction
                    if profile.annual_leave_balance <3:
                        notify_authorized_users_low_leave(user)
                else:
                    # Handle insufficient leave balance
                    messages.error(request, "Insufficient leave balance for deduction due to lateness.")
                    attendance.is_late = False
                    attendance.lateness_duration = None
                    deduction = 0
                messages.info(request, f"Late by {lateness_minutes} minutes. Deducted {deduction} days from your annual leave.")
            else:
                attendance.is_late = False
                attendance.lateness_duration = None

            attendance.save()
            # Create notification if late
            if attendance.is_late:
                notify_authorized_users_late(user, today, lateness, deduction)

            return redirect('personnel_dashboard')
    else:
        form = CheckInForm()

    context = {
        'form': form
    }
    return render(request, 'employees/attendance_check_in.html', context)


# problematic --> getting all users and filter authorized ones requires additional work
# notification object should be handled
def notify_authorized_users_late(employee, date, lateness, deduction):
    # Get all authorized users
    User = get_user_model() # import from model can also resolve the issue
    authorized_users = User.objects.filter(is_authorized=True)
    message = f"Employee {employee.username} was late on {date} by {lateness.seconds // 60} minutes and {deduction} days were deducted from their leave."
    for user in authorized_users:
        Notification.objects.create(recipient=user, message=message)


@login_required(login_url='personnel_login')
@user_passes_test(is_personnel)
def view_leave_balance(request):
    user = request.user
    profile = user.profile
    total_leave = float(profile.annual_leave_balance)  # Convert Decimal to float for arithmetic
    # Calculate granted leave doesn't count from
    approved_leave = LeaveRequest.objects.filter(employee=user, status='A').aggregate(total=Sum('days')).get('total') or 0
    approved_leave = float(approved_leave)  # Ensure it's a float
    remaining_leave = total_leave - approved_leave  # Calculate remaining leave
    
    context = {
        'total_leave': total_leave,
        'used_leave': approved_leave,
        'remaining_leave': remaining_leave  # Pass remaining_leave to the template
    }
    return render(request, 'employees/view_leave_balance.html', context)


@login_required(login_url='personnel_login')
@user_passes_test(is_personnel)
def request_leave(request):
    user = request.user
    profile = user.profile
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.employee = user
            # Calculate number of days
            leave_request.days = (leave_request.end_date - leave_request.start_date).days + 1
            # Check if sufficient leave balance
            if profile.annual_leave_balance >= leave_request.days:
                profile.annual_leave_balance -= leave_request.days
                profile.save()
                leave_request.save()
                # Notify Authorized Users
                notify_authorized_users_leave_request(leave_request)
                messages.success(request, "Leave request submitted successfully.")
                return redirect('view_leave_balance')
            else:
                messages.error(request, "Insufficient leave balance for the requested period.")
    else:
        form = LeaveRequestForm()
    context = {
        'form': form
    }
    return render(request, 'employees/request_leave.html', context)

def notify_authorized_users_leave_request(leave_request):
    User = get_user_model() # import from model can also resolve the issue
    authorized_users = User.objects.filter(is_authorized=True)
    message = f"Employee {leave_request.employee.username} has requested leave from {leave_request.start_date} to {leave_request.end_date} ({leave_request.days} days). Reason: {leave_request.reason}"
    for user in authorized_users:
        Notification.objects.create(recipient=user, message=message)

        
@login_required(login_url='authorized_login')
@user_passes_test(is_authorized_user)
def approve_leave(request, leave_id):
    leave_request = get_object_or_404(LeaveRequest, id=leave_id, status='P')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            leave_request.status = 'A'
            messages.success(request, "Leave request approved.")
        elif action == 'reject':
            # Refund the leave days if rejected
            profile = leave_request.employee.profile
            profile.annual_leave_balance += leave_request.days
            profile.save()
            leave_request.status = 'R'
            messages.success(request, "Leave request rejected.")
        leave_request.responded_at = timezone.now()
        leave_request.save()

        # Notify the employee about the decision
        notify_employee_leave_decision(leave_request)

        return redirect('view_pending_leave_requests')
    return render(request, 'employees/approve_leave.html', {'leave_request': leave_request})

@login_required(login_url='authorized_login')
@user_passes_test(is_authorized_user)
def view_pending_leave_requests(request):
    pending_requests = LeaveRequest.objects.filter(status='P').order_by('-requested_at')
    context = {
        'pending_requests': pending_requests
    }
    return render(request, 'employees/view_pending_leave_requests.html', context)

def notify_employee_leave_decision(leave_request):
    employee = leave_request.employee
    if leave_request.status == 'A':
        message = f"Your leave request from {leave_request.start_date} to {leave_request.end_date} has been approved."
    elif leave_request.status == 'R':
        message = f"Your leave request from {leave_request.start_date} to {leave_request.end_date} has been rejected."
    Notification.objects.create(recipient=employee, message=message)






def notify_authorized_users_low_leave(user):
    User = get_user_model() # import from model can also resolve the issue
    # Check if leave balance is below 3 days
    if user.profile.annual_leave_balance < 3:
        authorized_users = User.objects.filter(is_authorized=True)
        message = f"Employee {user.username} now has {user.profile.annual_leave_balance} days of annual leave remaining."
        for auth_user in authorized_users:
            Notification.objects.create(recipient=auth_user, message=message)


@login_required(login_url='personnel_login')
@user_passes_test(is_personnel)
def attendance_check_out(request):
    user = request.user
    today = timezone.now().date()
    now_time = timezone.now().time()

    try:
        attendance = AttendanceRecord.objects.get(employee=user, date=today)
    except AttendanceRecord.DoesNotExist:
        messages.error(request, "You haven't checked in today.")
        return redirect('personnel_dashboard')

    if attendance.last_check_out:
        messages.info(request, "You have already checked out today.")
        return redirect('personnel_dashboard')

    if request.method == 'POST':
        form = CheckOutForm(request.POST)
        if form.is_valid():
            check_out_time = form.cleaned_data.get('check_out_time') or now_time
            attendance.last_check_out = check_out_time
            attendance.save()
            messages.success(request, "Check-Out successful.")
            return redirect('personnel_dashboard')
    else:
        form = CheckOutForm()

    context = {
        'form': form
    }
    return render(request, 'employees/attendance_check_out.html', context)

@login_required(login_url='authorized_login')
@user_passes_test(is_authorized_user)
def view_attendance_records(request):
    records = AttendanceRecord.objects.select_related('employee').all().order_by('-date')
    
    # Search or filter functionality can be added here
    query = request.GET.get('q')
    if query:
        records = records.filter(
            Q(employee__username__icontains=query) |
            Q(employee__profile__full_name__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(records, 20)  # Show 20 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'employees/view_attendance_records.html', context)


@login_required(login_url='authorized_login')
@user_passes_test(is_authorized_user)
def view_monthly_reports(request):
    reports = MonthlyReport.objects.select_related('employee').all().order_by('-year', '-month')
    
    # Search or filter functionality can be added here
    query = request.GET.get('q')
    if query:
        reports = reports.filter(
            Q(employee__username__icontains=query) |
            Q(employee__profile__full_name__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(reports, 20)  # Show 20 reports per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'employees/view_monthly_reports.html', context)