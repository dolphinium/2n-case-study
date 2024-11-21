from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmployeeProfile, AttendanceRecord, LeaveRequest, Notification, MonthlyReport

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('is_authorized',)}),
    )

admin.site.register(User, UserAdmin)
admin.site.register(EmployeeProfile)
admin.site.register(AttendanceRecord)
admin.site.register(LeaveRequest)
admin.site.register(Notification)
admin.site.register(MonthlyReport)