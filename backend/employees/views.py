from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .decorators import personnel_required, authorized_user_required    # custom decorators
from .forms import CheckInForm, CheckOutForm
from .models import AttendanceRecord
from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator

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
    return render(request, 'employees/authorized_dashboard.html')

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
            else:
                attendance.is_late = False
                attendance.lateness_duration = None

            attendance.save()
            messages.success(request, "Check-In successful.")
            return redirect('personnel_dashboard')
    else:
        form = CheckInForm()

    context = {
        'form': form
    }
    return render(request, 'employees/attendance_check_in.html', context)

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