from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Resident, Staff, Technician

class ResidentInline(admin.StackedInline):
    model = Resident
    can_delete = False
    verbose_name_plural = 'Resident Profile'

class StaffInline(admin.StackedInline):
    model = Staff
    can_delete = False
    verbose_name_plural = 'Staff Profile'

class TechnicianInline(admin.StackedInline):
    model = Technician
    can_delete = False
    verbose_name_plural = 'Technician Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (ResidentInline, StaffInline, TechnicianInline)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    
    def get_role(self, obj):
        if obj.is_resident: return "Resident"
        if obj.is_staff_member: return "Staff"
        if obj.is_technician: return "Technician"
        return "Admin/User"
    get_role.short_description = 'Role'

admin.site.register(User, CustomUserAdmin)
admin.site.register(Resident)
admin.site.register(Staff)
admin.site.register(Technician)
