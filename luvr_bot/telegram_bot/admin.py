
import datetime
import os

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ExportActionMixin
from import_export.resources import ModelResource
from import_export.fields import Field
from import_export.formats import base_formats
from dotenv import load_dotenv
from telegram import Bot
from typing import List

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
bot = Bot(token=token)

from .models import Employee, EmployeeGeoPosition, Branch, JobRequest, JobRequestAssignment, Shift, Company, CustomUser, \
    ProxyShift, EmployeeList


class JobRequestAssignmentInline(admin.TabularInline):
    model = JobRequestAssignment


class ShiftInline(admin.TabularInline):
    model = Shift


class BranchInline(admin.TabularInline):
    model = Branch


class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'language', 'jumis_go_user_id', 'token', 'password', 'chat_id', 'INN', 'full_name',
                    'city')
    inlines = [JobRequestAssignmentInline]
    readonly_fields = ['chat_id']


class EmployeeGeoPositionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'latitude', 'longitude', 'geo_positions_date',)
    readonly_fields = ['latitude', 'longitude', 'geo_positions_date']


class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_name', 'latitude', 'longitude', 'address', 'company')

    def get_queryset(self, request):
        qs = super(BranchAdmin, self).get_queryset(request)
        if request.user.has_group('Manager'):
            return qs.filter(company=request.user.user_company)
        return qs


class JobRequestAdmin(admin.ModelAdmin):
    list_display = ('branch', 'employee_position', 'request_type', 'INN', 'employee_full_name', 'personalized_request',
                    'date_start', 'date_end', 'shift_time_start', 'shift_time_end', 'number_of_employees',
                    'request_comment', 'status', 'request_date', 'readable_broadcast')
    inlines = [JobRequestAssignmentInline]
    readonly_fields = ('last_notified_date', 'last_notification_status')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'branch' and request.user.has_group('Manager'):
            kwargs['queryset'] = Branch.objects.filter(company=request.user.user_company)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj: JobRequest, form, change):
        if request.user.is_superuser or request.user.has_group('Distributor') or (request.user.has_group('Manager') and obj.branch.company == request.user.user_company):
            super(JobRequestAdmin, self).save_model(request, obj, form, change)
        else:
            raise Exception('У Вас нет прав на это действие')

    def get_queryset(self, request):
        qs = super(JobRequestAdmin, self).get_queryset(request)
        if request.user.has_group('Manager'):
            return qs.filter(branch__company=request.user.user_company)
        return qs

    def get_readonly_fields(self, request, obj=None):
        return ['last_notified_date', 'last_notification_status', 'readable_broadcast']


class JobRequestAssignmentAdmin(admin.ModelAdmin):
    list_display = ('job_request', 'employee', 'status', 'assignment_date', )
    inlines = [ShiftInline]

    def save_model(self, request, obj: JobRequestAssignment, form, change):
        if request.user.is_superuser or request.user.has_group('Distributor') or (request.user.has_group('Manager') and obj.job_request.branch.company == request.user.user_company):
            super(JobRequestAssignmentAdmin, self).save_model(request, obj, form, change)
        else:
            raise Exception('У Вас нет прав на это действие')

    def get_queryset(self, request):
        qs = super(JobRequestAssignmentAdmin, self).get_queryset(request)
        if request.user.has_group('Manager'):
            return qs.filter(job_request__branch__company=request.user.user_company)
        return qs

    def delete_model(self, request, obj: JobRequestAssignment):
        date_str = datetime.datetime.strftime(obj.assignment_date, '%d.%m.%Y')
        # todo if do not send if there is no chat_id
        bot.send_message(chat_id=obj.employee.chat_id,
                         text=f'Ваше назначение на должность {obj.job_request.employee_position} '
                              f'на дату {date_str} было удалено.\nОбратитесь к менеджеру')
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        objects: List[JobRequestAssignment] = queryset.all()
        for assignment in objects:
            # todo if do not send if there is no chat_id
            date_str = datetime.datetime.strftime(assignment.assignment_date, '%d.%m.%Y')
            bot.send_message(chat_id=assignment.employee.chat_id,
                             text=f'Ваше назначение на должность {assignment.job_request.employee_position} '
                                  f'на дату {date_str} было удалено.\nОбратитесь к менеджеру')
        super().delete_queryset(request, queryset)


class ShiftAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'start_position', 'end_position', 'shift_date')
    readonly_fields = ['start_position', 'end_position']

    def save_model(self, request, obj: Shift, form, change):
        if request.user.is_superuser or request.user.has_group('Distributor') or (request.user.has_group('Manager')
                                                                                  and obj.assignment.job_request.branch.company == request.user.user_company):
            super(ShiftAdmin, self).save_model(request, obj, form, change)
        else:
            raise Exception('У Вас нет прав на это действие')

    def get_queryset(self, request):
        qs = super(ShiftAdmin, self).get_queryset(request)
        if request.user.has_group('Manager'):
            return qs.filter(assignment__job_request__branch__company=request.user.user_company)
        return qs


class ProxyShiftModelResource(ModelResource):
    employee = Field(attribute='Сотрудник', column_name='Сотрудник')
    position = Field(attribute='Функция', column_name='Функция')
    iin = Field(attribute='ИИН', column_name='ИИН')
    company = Field(attribute='Контрагент', column_name='Контрагент')
    branch = Field(attribute='Организация', column_name='Организация')
    planned_shift_start = Field(attribute='Плановое начало смены', column_name='Плановое начало смены')
    planned_shift_end = Field(attribute='Плановое окончание смены', column_name='Плановое окончание смены')
    actual_shift_start = Field(attribute='Отметка на приход', column_name='Отметка на приход')
    actual_shift_end = Field(attribute='Отметка на уход', column_name='Отметка на уход')
    date = Field(attribute='Дата табеля', column_name='Дата табеля')

    def dehydrate_employee(self, shift):
        return shift.readable_employee()

    def dehydrate_position(self, shift):
        return shift.readable_position()

    def dehydrate_iin(self, shift):
        return shift.readable_inn()

    def dehydrate_company(self, shift):
        return shift.readable_company()

    def dehydrate_branch(self, shift):
        return shift.readable_branch()

    def dehydrate_planned_shift_start(self, shift):
        planned_start = shift.readable_planned_shift_start()
        planned_start = datetime.time.strftime(planned_start, '%H:%M')

        return planned_start

    def dehydrate_planned_shift_end(self, shift):
        planned_end = shift.readable_planned_shift_end()
        planned_end = datetime.time.strftime(planned_end, '%H:%M')

        return planned_end

    def dehydrate_actual_shift_start(self, shift):
        actual_start = shift.readable_actual_shift_start()
        if actual_start:
            actual_start = datetime.time.strftime(actual_start, '%H:%M')
        else:
            actual_start = None

        return actual_start

    def dehydrate_actual_shift_end(self, shift):
        actual_end = shift.readable_actual_shift_end()
        if actual_end:
            actual_end = datetime.time.strftime(actual_end, '%H:%M')
        else:
            actual_end = None

        return actual_end

    def dehydrate_date(self, shift):
        shift_date = shift.readable_date()
        shift_date = datetime.date.strftime(shift_date, '%d.%m.%Y')

        return shift_date

    class Meta:
        model = ProxyShift
        exclude = ('id', )
        fields = ('readable_employee', 'readable_position', 'readable_inn', 'readable_company',
                  'readable_planned_shift_start', 'readable_planned_shift_end', 'readable_branch',
                  'readable_actual_shift_start', 'readable_actual_shift_end', 'readable_date',)


class ProxyShiftAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('readable_employee', 'readable_position', 'readable_inn', 'readable_company',
                    'readable_planned_shift_start', 'readable_planned_shift_end', 'readable_branch',
                    'readable_actual_shift_start', 'readable_actual_shift_end', 'readable_date', )
    resource_class = ProxyShiftModelResource

    def get_export_formats(self):
        formats = (
            base_formats.XLSX,
        )
        return [f for f in formats if f().can_export()]

    def get_queryset(self, request):
        qs = super(ProxyShiftAdmin, self).get_queryset(request)
        if request.user.has_group('Manager'):
            return qs.filter(assignment__job_request__branch__company=request.user.user_company)
        return qs


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', )
    inlines = [BranchInline]

    def save_model(self, request, obj: Company, form, change):
        if request.user.is_superuser or request.user.has_group('Distributor') or (request.user.has_group('Manager') and obj.name == request.user.user_company):
            super(CompanyAdmin, self).save_model(request, obj, form, change)
        else:
            raise Exception('У Вас нет прав на это действие')

    def get_queryset(self, request):
        qs = super(CompanyAdmin, self).get_queryset(request)
        if request.user.has_group('Manager'):
            return qs.filter(name=request.user.user_company)
        return qs


class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('user_company', )
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("user_company",)}),)


class EmployeeListAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'inn', )


admin.site.register(Employee, EmployeeAdmin)
admin.site.register(EmployeeGeoPosition, EmployeeGeoPositionAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(JobRequest, JobRequestAdmin)
admin.site.register(JobRequestAssignment, JobRequestAssignmentAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ProxyShift, ProxyShiftAdmin)
admin.site.register(EmployeeList, EmployeeListAdmin)
