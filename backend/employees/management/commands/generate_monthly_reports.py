from django.core.management.base import BaseCommand
from employees.models import AttendanceRecord, MonthlyReport, User
from django.utils import timezone
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Generate monthly attendance reports for all employees.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        # Get the previous month
        first_day_of_current_month = today.replace(day=1)
        last_month = first_day_of_current_month - timedelta(days=1)
        month = last_month.month
        year = last_month.year

        for user in User.objects.filter(is_authorized=False):
            attendance_records = AttendanceRecord.objects.filter(
                employee=user,
                date__month=month,
                date__year=year
            )
            total_seconds = 0
            for record in attendance_records:
                if record.first_check_in and record.last_check_out:
                    check_in = datetime.combine(record.date, record.first_check_in)
                    check_out = datetime.combine(record.date, record.last_check_out)
                    duration = check_out - check_in
                    total_seconds += duration.total_seconds()
            total_working_hours = timedelta(seconds=total_seconds)
            # Create or update the MonthlyReport
            report, created = MonthlyReport.objects.update_or_create(
                employee=user,
                month=month,
                year=year,
                defaults={'total_working_hours': total_working_hours}
            )
            self.stdout.write(self.style.SUCCESS(
                f"Report {'created' if created else 'updated'} for {user.username} for {month}/{year}"
            ))