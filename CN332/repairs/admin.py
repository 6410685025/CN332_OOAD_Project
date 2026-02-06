from django.contrib import admin
from .models import RepairRequest, WorkLog

class WorkLogInline(admin.TabularInline):
    model = WorkLog
    extra = 1

@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_type', 'resident', 'location', 'status', 'technician', 'created_at')
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('description', 'resident__user__username', 'location')
    inlines = [WorkLogInline]

@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ('repair_request', 'timestamp', 'description')
