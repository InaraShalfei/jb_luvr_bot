# Generated by Django 4.2.1 on 2023-07-04 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0030_alter_employee_token'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmployeeList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=100, verbose_name='ФИО')),
                ('id_number', models.CharField(max_length=12, verbose_name='ИИН')),
            ],
            options={
                'verbose_name': 'Список сотрудников',
                'verbose_name_plural': 'Списки сотрудников',
            },
        ),
    ]
