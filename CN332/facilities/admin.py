from django.contrib import admin
from .models import Facility, Booking

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'facility_type', 'capacity')
    list_filter = ('facility_type',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('resident', 'facility', 'booking_date', 'time_slot', 'status')
    list_filter = ('status', 'booking_date', 'facility')
    search_fields = ('resident__user__username',)
