# Generated by Django 4.2.1 on 2023-06-07 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0015_alter_employee_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='phone_number',
            field=models.CharField(max_length=11, unique=True, verbose_name='номер телефона'),
        ),
    ]
