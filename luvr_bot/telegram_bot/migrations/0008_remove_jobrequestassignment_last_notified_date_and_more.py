# Generated by Django 4.2.1 on 2023-06-01 04:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0007_jobrequestassignment_last_notified_date'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobrequestassignment',
            name='last_notified_date',
        ),
        migrations.AddField(
            model_name='jobrequest',
            name='last_notification_status',
            field=models.CharField(blank=True, max_length=300, null=True, verbose_name='статус уведомления'),
        ),
    ]
