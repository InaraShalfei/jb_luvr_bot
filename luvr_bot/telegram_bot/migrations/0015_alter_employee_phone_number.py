# Generated by Django 4.2.1 on 2023-06-07 10:23

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0014_alter_employee_phone_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='phone_number',
            field=models.CharField(max_length=11, validators=[django.core.validators.MinLengthValidator(11)], verbose_name='номер телефона'),
        ),
    ]
