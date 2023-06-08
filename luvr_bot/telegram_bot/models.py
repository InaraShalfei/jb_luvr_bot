import datetime

from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.utils.html import format_html

from django.db import models
from django.contrib import admin
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError


from .constants import statuses_dict


class Employee(models.Model):
    phone_number = models.CharField(unique=True, max_length=11, verbose_name='номер телефона', validators=[MinLengthValidator(3)])
    chat_id = models.IntegerField(verbose_name='ID телеграм чата', blank=True, null=True)
    INN = models.CharField(max_length=12, verbose_name='ИНН сотрудника', null=True, blank=True)
    full_name = models.CharField(max_length=12, verbose_name='ФИО сотрудника', null=True, blank=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return self.phone_number

    def clean(self):
        if not str(self.phone_number).isdigit():
            raise ValidationError('Не допускаются другие элементы, кроме цифр')
        elif len(self.phone_number) < 11:
            raise ValidationError('Номер не должен быть менее 11 цифр')

    def save(self, *args, **kwargs):
        self.phone_number = '7' + self.phone_number[-10:]
        super().save(*args, **kwargs)


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
        ('CLOSED', 'Закрыта'),
        ('NEW', 'Новая')
    ]
    REQUEST_TYPES = [
        ('FOR_DATE', 'На дату'),
        ('FOR_PERIOD', 'На период')
    ]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='job_requests', verbose_name='филиал')
    personalized_request = models.BooleanField(blank=True, null=True, default=False, verbose_name='именная заявка')
    employee_full_name = models.CharField(max_length=300, blank=True, null=True, verbose_name='ФИО сотрудника')
    INN = models.CharField(max_length=12, verbose_name='ИНН сотрудника', null=True, blank=True)
    status = models.CharField(max_length=250, choices=STATUSES, blank=True, null=True, verbose_name='статус заявки',
                              default='NEW')
    employee_position = models.CharField(blank=True, null=True, max_length=300, verbose_name='должность')
    request_type = models.CharField(blank=True, null=True, choices=REQUEST_TYPES, max_length=250, verbose_name='тип заявки')
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
        request_date = self.request_date + datetime.timedelta(hours=6)
        date_str = datetime.datetime.strftime(request_date, '%d.%m.%Y %H:%M')
        return f'Заявка от {date_str}'

    @admin.display(description='Статус')
    def readable_notification_status(self):
        return statuses_dict[self.last_notification_status] if self.last_notification_status \
                                                               in statuses_dict else self.last_notification_status

    @admin.display(description='Рассылка')
    def readable_broadcast(self):
        date_start = datetime.datetime.strftime(self.date_start, '%d.%m.%Y') if self.date_start else ''
        date_end = datetime.datetime.strftime(self.date_end, '%d.%m.%Y') if self.date_end else ''
        time_start = datetime.time.strftime(self.shift_time_start, '%H:%M') if self.shift_time_start else ''
        time_end = datetime.time.strftime(self.shift_time_end, '%H:%M') if self.shift_time_end else ''

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
            if shift_end <= shift_start:
                shift_end += delta
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

    def clean(self):
        max_assignments = ((self.job_request.date_end - self.job_request.date_start).days + 1) * int(self.job_request.number_of_employees)

        if self.job_request.assignments.count() >= max_assignments:
            raise ValidationError('Для данной заявки нельзя больше создать назначения!')

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


class ProxyShift(Shift):
    class Meta:
        proxy = True
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчет'

    @admin.display(description='сотрудник')
    def readable_employee(self):
        return self.assignment.employee.full_name

    @admin.display(description='ИИН')
    def readable_inn(self):
        return self.assignment.employee.INN

    @admin.display(description='функция')
    def readable_position(self):
        return self.assignment.job_request.employee_position

    @admin.display(description='контрагент')
    def readable_company(self):
        return self.assignment.job_request.branch.company

    @admin.display(description='организация')
    def readable_branch(self):
        return self.assignment.job_request.branch

    @admin.display(description='дата табеля')
    def readable_date(self):
        return self.shift_date

    @admin.display(description='плановое начало смены')
    def readable_planned_shift_start(self):
        return self.assignment.job_request.shift_time_start

    @admin.display(description='плановое окончание смены')
    def readable_planned_shift_end(self):
        return self.assignment.job_request.shift_time_end

    @admin.display(description='отметка на приход')
    def readable_actual_shift_start(self):
        planned_time = self.assignment.job_request.shift_time_start
        if self.start_position:
            actual_time = (self.start_position.geo_positions_date + timedelta(hours=6)).time()
            max_start_time = max(planned_time, actual_time)
        else:
            max_start_time = None
        return max_start_time

    @admin.display(description='отметка на уход')
    def readable_actual_shift_end(self):
        planned_time = self.assignment.job_request.shift_time_end
        if self.end_position:
            actual_time = (self.end_position.geo_positions_date + timedelta(hours=6)).time()
            min_end_time = min(planned_time, actual_time)
        else:
            min_end_time = None
        return min_end_time


class CustomUser(AbstractUser):
    user_company = models.ForeignKey(Company, on_delete=models.CASCADE, blank=True, null=True, verbose_name='компания пользователя')

    def has_group(self, group_name):
        return self.groups.filter(name=group_name).exists()
