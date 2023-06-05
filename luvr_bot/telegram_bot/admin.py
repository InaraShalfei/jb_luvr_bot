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
    list_display = ('branch', 'employee_position', 'request_type', 'INN', 'employee_full_name', 'personalized_request', 'date_start', 'date_end', 'shift_time_start',
                    'shift_time_end', 'number_of_employees', 'request_comment', 'status', 'request_date',
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

    def get_readonly_fields(self, request, obj=None):
        if request.user.has_group('Distributor'):
            return ['branch', 'employee_position', 'request_type', 'date_start', 'date_end', 'shift_time_start',
                    'shift_time_end', 'number_of_employees', 'request_comment', 'request_date',
                    'readable_broadcast']
        return ['status']


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
