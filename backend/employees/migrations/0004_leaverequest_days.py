# Generated by Django 4.2.16 on 2024-11-22 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("employees", "0003_alter_employeeprofile_annual_leave_balance"),
    ]

    operations = [
        migrations.AddField(
            model_name="leaverequest",
            name="days",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=5),
        ),
    ]