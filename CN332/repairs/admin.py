from django.contrib import admin
from .models import RepairRequest, WorkLog, RepairImage, RepairStatusUpdate

class WorkLogInline(admin.TabularInline):
    model = WorkLog
    extra = 1

class RepairImageInline(admin.TabularInline):
    model = RepairImage
    extra = 1

class RepairStatusUpdateInline(admin.TabularInline):
    model = RepairStatusUpdate
    extra = 0

@admin.register(RepairRequest)
class RepairRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'request_type', 'resident', 'location', 'status', 'technician', 'created_at')
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('description', 'resident__user__username', 'location')
    inlines = [WorkLogInline, RepairImageInline, RepairStatusUpdateInline]

@admin.register(WorkLog)
class WorkLogAdmin(admin.ModelAdmin):
    list_display = ('repair_request', 'timestamp', 'description')

@admin.register(RepairImage)
class RepairImageAdmin(admin.ModelAdmin):
    list_display = ('repair_request', 'image_type', 'uploaded_at', 'uploaded_by')
    list_filter = ('image_type', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

