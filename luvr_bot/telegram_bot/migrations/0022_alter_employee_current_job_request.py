# Generated by Django 4.2.1 on 2023-06-12 06:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0021_employee_current_job_request_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='current_job_request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='telegram_bot.jobrequest', verbose_name='текущая заявка'),
        ),
    ]