from django.contrib import admin
from .models import LostFound

@admin.register(LostFound)
class LostFoundAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'item_type', 'status', 'reporter', 'claimant', 'location', 'reported_at')
    list_filter = ('item_type', 'status', 'reported_at')
    search_fields = ('item_name', 'description')
