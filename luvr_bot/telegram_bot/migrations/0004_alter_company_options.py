# Generated by Django 4.2.1 on 2023-05-30 11:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('telegram_bot', '0003_company_jobrequest_message_text_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='company',
            options={'verbose_name': 'Компания', 'verbose_name_plural': 'Компании'},
        ),
    ]
