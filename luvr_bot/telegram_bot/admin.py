from django.contrib import admin

from .models import Employee, EmployeeGeoPosition, Branch, JobRequest, JobRequestAssignment, Shift, Company
from import_export.admin import ExportActionMixin
from import_export.resources import ModelResource


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


class JobRequestModelResource(ModelResource):
    class Meta:
        model = JobRequest
        exclude = ('id', )
        fields = ('branch__branch_name', 'branch__address', 'employee_position', 'request_type', 'date_start', 'date_end', 'shift_time_start',
                  'shift_time_end', 'number_of_employees', 'request_comment', 'employee', 'status', 'request_date',
                  'readable_broadcast')

    def get_export_headers(self):
        headers = []
        for field in self.get_fields():
            model_fields = self.Meta.model._meta.get_fields()
            header = next((x.verbose_name for x in model_fields if x.name == field.column_name), field.column_name)
            headers.append(header)
        return headers


class JobRequestAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('branch', 'employee_position', 'request_type', 'date_start', 'date_end', 'shift_time_start',
                    'shift_time_end', 'number_of_employees', 'request_comment', 'employee', 'status', 'request_date',
                    'readable_broadcast')
    inlines = [JobRequestAssignmentInline]
    resource_class = JobRequestModelResource


class JobRequestAssignmentAdmin(admin.ModelAdmin):
    list_display = ('job_request', 'employee', 'status', 'assignment_date', )
    inlines = [ShiftInline]


class ShiftAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'start_position', 'end_position', 'shift_date')


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', )
    inlines = [BranchInline]


admin.site.register(Employee, EmployeeAdmin)
admin.site.register(EmployeeGeoPosition, EmployeeGeoPositionAdmin)
admin.site.register(Branch, BranchAdmin)
admin.site.register(JobRequest, JobRequestAdmin)
admin.site.register(JobRequestAssignment, JobRequestAssignmentAdmin)
admin.site.register(Shift, ShiftAdmin)
admin.site.register(Company, CompanyAdmin)
# admin.site.register(CustomUser)
