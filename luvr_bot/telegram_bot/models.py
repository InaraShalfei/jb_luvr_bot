import datetime
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.utils.html import format_html

from django.db import models
from django.contrib import admin

from .constants import statuses_dict


class Employee(models.Model):
    phone_number = models.CharField(max_length=250, verbose_name='номер телефона')
    chat_id = models.IntegerField(verbose_name='ID телеграм чата', blank=True, null=True)
    INN = models.CharField(max_length=12, verbose_name='ИНН сотрудника', null=True, blank=True)
    full_name = models.CharField(max_length=12, verbose_name='ФИО сотрудника', null=True, blank=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return self.phone_number


class EmployeeGeoPosition(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='geo_positions', verbose_name='сотрудник')
    latitude = models.CharField(max_length=300, verbose_name='широта')
    longitude = models.CharField(max_length=300, verbose_name='долгота')
    geo_positions_date = models.DateTimeField(auto_now=True, verbose_name='дата внесения гео позиций')

    class Meta:
        verbose_name = 'Геопозиция сотрудника'
        verbose_name_plural = 'Геопозиция сотрудников'

    def __str__(self):
        return f'{self.latitude} - {self.longitude}'


class Company(models.Model):
    name = models.CharField(max_length=250,  verbose_name='название компании')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Компания'
        verbose_name_plural = 'Компании'


class Branch(models.Model):
    branch_name = models.CharField(max_length=250,  verbose_name='название филиала')
    latitude = models.CharField(max_length=300,  verbose_name='широта')
    longitude = models.CharField(max_length=300,  verbose_name='долгота')
    address = models.CharField(max_length=300, verbose_name='адрес', blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='brances', verbose_name='компания',
                                blank=True, null=True)

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'

    def __str__(self):
        return f'{self.branch_name} {self.address}'


class JobRequest(models.Model):
    STATUSES = [
        ('APPROVED', 'Принята'),
        ('REJECTED', 'Отклонена'),
        ('CANCELED', 'Отменена'),
        ('CLOSED', 'Закрыта')
    ]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='job_requests', verbose_name='филиал')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='job_requests', verbose_name='сотрудник',
                                 blank=True, null=True)
    status = models.CharField(max_length=250, choices=STATUSES, blank=True, null=True, verbose_name='статус заявки')
    employee_position = models.CharField(blank=True, null=True, max_length=300, verbose_name='должность')
    request_type = models.CharField(blank=True, null=True, max_length=250, verbose_name='тип заявки')
    date_start = models.DateField(blank=True, null=True, verbose_name='дата начала периода')
    date_end = models.DateField(blank=True, null=True, verbose_name='дата окончания периода')
    shift_time_start = models.TimeField(blank=True, null=True, verbose_name='время начала смены')
    shift_time_end = models.TimeField(blank=True, null=True, verbose_name='время окончания смены')
    number_of_employees = models.CharField(max_length=3, blank=True, null=True, verbose_name='количество сотрудников')
    request_comment = models.TextField(blank=True, null=True, verbose_name='комментарий')
    request_date = models.DateTimeField(auto_now=True, verbose_name='дата заявки')
    last_notified_date = models.DateField(blank=True, null=True, verbose_name='дата последнего уведомления')
    last_notification_status = models.CharField(max_length=300, blank=True, null=True, verbose_name='статус уведомления')

    class Meta:
        verbose_name = 'Заявка на сотрудников'
        verbose_name_plural = 'Заявки на сотрудников'

    def __str__(self):
        date_str = datetime.datetime.strftime(self.request_date, '%d.%m.%Y %H:%M')
        return f'Заявка от {date_str}'

    @admin.display(description='Статус')
    def readable_notification_status(self):
        return statuses_dict[self.last_notification_status] if self.last_notification_status \
                                                               in statuses_dict else self.last_notification_status

    @admin.display(description='Рассылка')
    def readable_broadcast(self):
        date_start = datetime.datetime.strftime(self.date_start, '%d.%m.%Y')
        date_end = datetime.datetime.strftime(self.date_end, '%d.%m.%Y')
        time_start = datetime.time.strftime(self.shift_time_start, '%H:%M')
        time_end = datetime.time.strftime(self.shift_time_end, '%H:%M')

        return format_html(f'{self.branch}<br>📌{self.employee_position}<br>🕐{time_start} - {time_end}<br>'
                           f'🔴Дата: {date_start} - {date_end}<br>✅Оплата: 1000 тнг/час')

    def is_shift_includes_time(self, request_date_time, tolerance_minutes=30):
        dates = []
        delta = timedelta(days=1)
        start_date = self.date_start
        while start_date <= self.date_end:
            dates.append(start_date)
            start_date += delta

        for date in dates:
            shift_start = datetime.datetime.combine(date, self.shift_time_start) - timedelta(minutes=tolerance_minutes)
            shift_end = datetime.datetime.combine(date, self.shift_time_end) + timedelta(minutes=tolerance_minutes)
            if shift_start <= request_date_time <= shift_end:
                return True
        return False


class JobRequestAssignment(models.Model):
    STATUSES = [
        ('ADMITTED', 'Подтверждено'),
        ('NOT ADMITTED', 'Неподтверждено'),
    ]
    job_request = models.ForeignKey(JobRequest, on_delete=models.CASCADE, related_name='assignments',
                                    verbose_name='заявка на сотрудника')
    status = models.CharField(max_length=250, choices=STATUSES, blank=True, null=True, verbose_name='статус назначения')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='assignments',
                                 verbose_name='сотрудник')
    assignment_date = models.DateTimeField(auto_now=True, verbose_name='дата назначения')

    class Meta:
        verbose_name = 'Назначение сотрудников'
        verbose_name_plural = 'Назначения сотрудников'

    def __str__(self):
        date_str = datetime.datetime.strftime(self.assignment_date, '%d.%m.%Y %H:%M')
        return f'Назначение от {date_str}'

    def get_shift_for_date(self, date):
        for shift in self.shifts.all():
            if shift.shift_date == date:
                return shift
        return None


class Shift(models.Model):
    start_position = models.ForeignKey(EmployeeGeoPosition, on_delete=models.CASCADE, blank=True, null=True,
                                       related_name='start_assignments', verbose_name='начало смены')
    end_position = models.ForeignKey(EmployeeGeoPosition, on_delete=models.CASCADE, blank=True, null=True,
                                     related_name='end_assignments', verbose_name='окончание смены')
    shift_date = models.DateField(auto_now=True, verbose_name='дата смены')
    assignment = models.ForeignKey(JobRequestAssignment, on_delete=models.CASCADE, related_name='shifts',
                                   verbose_name='назначение')

    class Meta:
        verbose_name = 'Смена'
        verbose_name_plural = 'Смены'

    def __str__(self):
        date_str = datetime.datetime.strftime(self.shift_date, '%d.%m.%Y %H:%M')
        return f'Смена от {date_str}'


class CustomUser(AbstractUser):
    user_company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True, verbose_name='компания пользователя')
