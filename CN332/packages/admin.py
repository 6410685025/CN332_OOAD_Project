from django.contrib import admin
from .models import Package

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'resident', 'status', 'arrived_at', 'picked_up_at', 'handled_by')
    list_filter = ('status', 'arrived_at')
    search_fields = ('sender', 'resident__user__username', 'resident__room_number')
