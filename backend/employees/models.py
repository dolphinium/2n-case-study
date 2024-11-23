from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    is_authorized = models.BooleanField(default=False)

    def __str__(self):
        return self.username
    
class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    annual_leave_balance = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)

    def __str__(self):
        return self.full_name
    
class AttendanceRecord(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    first_check_in = models.TimeField(null=True, blank=True)
    last_check_out = models.TimeField(null=True, blank=True)
    is_late = models.BooleanField(default=False)
    lateness_duration = models.DurationField(null=True, blank=True)
    leave_deducted = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.employee.username} - {self.date}"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pending'),
        ('A', 'Approved'),
        ('R', 'Rejected'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    days = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  
    
    def __str__(self):
        return f"{self.employee.username} - {self.get_status_display()} from {self.start_date} to {self.end_date}"
    
    def save(self, *args, **kwargs):
        # Calculate number of days upon saving
        self.days = (self.end_date - self.start_date).days + 1
        super().save(*args, **kwargs)
    

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification to {self.recipient.username} at {self.timestamp}"
    
class MonthlyReport(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='monthly_reports')
    month = models.IntegerField()
    year = models.IntegerField()
    total_working_hours = models.DurationField()

    class Meta:
        unique_together = ('employee', 'month', 'year')

    def __str__(self):
        return f"{self.employee.username} - {self.month}/{self.year}"