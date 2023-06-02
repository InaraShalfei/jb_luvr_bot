from django.contrib import admin

from .models import Employee, EmployeeGeoPosition, Branch, JobRequest, JobRequestAssignment, Shift, Company, CustomUser
from django.contrib.auth.admin import UserAdmin


class JobRequestAssignmentInline(admin.TabularInline):
    model = JobRequestAssignment


class ShiftInline(admin.TabularInline):
    model = Shift


class BranchInline(admin.TabularInline):
    model = Branch


class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'chat_id', 'INN', 'full_name',)
    inlines = [JobRequestAssignmentInline]


class EmployeeGeoPositionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'latitude', 'longitude', 'geo_positions_date',)


class BranchAdmin(admin.ModelAdmin):
    list_display = ('branch_name', 'latitude', 'longitude', 'address', 'company')


class JobRequestAdmin(admin.ModelAdmin):
    list_display = ('branch', 'employee_position', 'request_type', 'date_start', 'date_end', 'shift_time_start',
                    'shift_time_end', 'number_of_employees', 'request_comment', 'employee', 'status', 'request_date',
                    'readable_broadcast')
    inlines = [JobRequestAssignmentInline]

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


class JobRequestAssignmentAdmin(admin.ModelAdmin):
    list_display = ('job_request', 'employee', 'status', 'assignment_date', )
    inlines = [ShiftInline]


class ShiftAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'start_position', 'end_position', 'shift_date')


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', )
    inlines = [BranchInline]


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'user_company')


admin.site.register(Employee, EmployeeAdmin)
admin.site.register(EmployeeGeoPosition, EmployeeGeoPositionAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(JobRequest, JobRequestAdmin)
admin.site.register(JobRequestAssignment, JobRequestAssignmentAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Company, CompanyAdmin)

admin.site.register(CustomUser, CustomUserAdmin)
