# Generated by Django 4.2.1 on 2023-06-01 08:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0008_remove_jobrequestassignment_last_notified_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobrequest',
            name='message_text',
        ),
    ]
