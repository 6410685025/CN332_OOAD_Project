from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from .models import Facility, Booking
from .forms import BookingForm, FacilityForm

@login_required
def facility_list_view(request):
    facilities = Facility.objects.all()
    today = timezone.localdate()
    time_slots = [
        '09:00-10:00',
        '10:00-11:00',
        '11:00-12:00',
        '13:00-14:00',
        '14:00-15:00',
        '15:00-16:00',
        '16:00-17:00',
    ]
    booked_slots = (
        Booking.objects.filter(booking_date=today)
        .exclude(status='CANCELLED')
        .values_list('facility_id', 'time_slot')
        .distinct()
    )
    facility_slot_map = {}
    for facility_id, time_slot in booked_slots:
        facility_slot_map.setdefault(facility_id, set()).add(time_slot)
    unavailable_facility_ids = [
        facility_id
        for facility_id, slots in facility_slot_map.items()
        if len(slots) >= len(time_slots)
    ]
    my_bookings = []
    if request.user.is_resident:
        my_bookings = list(Booking.objects.filter(
            resident=request.user.resident
        ).exclude(status='CANCELLED').select_related('facility').order_by('booking_date')[:5])
    return render(request, 'facilities/facility_list.html', {
        'facilities': facilities,
        'unavailable_facility_ids': unavailable_facility_ids,
        'my_bookings': my_bookings,
        'is_resident': request.user.is_resident,
    })

@login_required
def create_booking_view(request):
    if not request.user.is_resident:
        return redirect('dashboard')
    
    facility_id = request.GET.get('facility')
    if facility_id:
        try:
            facility = Facility.objects.get(pk=facility_id)
            if not facility.is_open:
                return redirect('facility_list')
        except Facility.DoesNotExist:
            pass
    
    time_slot_values = [
        '09:00-10:00',
        '10:00-11:00',
        '11:00-12:00',
        '12:00-13:00',
        '13:00-14:00',
        '14:00-15:00',
        '15:00-16:00',
        '16:00-17:00',
        '17:00-18:00',
        '18:00-19:00',
        '19:00-20:00',
        '20:00-21:00',
        '21:00-22:00',
    ]
    def format_slot_label(value):
        start = value.split('-')[0]
        hour, minute = start.split(':')
        hour = int(hour)
        suffix = 'AM' if hour < 12 else 'PM'
        display_hour = hour if 1 <= hour <= 12 else hour - 12
        return f"{display_hour}:{minute} {suffix}"

    time_slots = [
        {'value': value, 'label': format_slot_label(value)}
        for value in time_slot_values
    ]
    selected_facility = None
    selected_date = None
    booked_slots = []
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.resident = request.user.resident
            booking.save()
            return redirect('my_bookings')
    else:
        facility_id = request.GET.get('facility')
        selected_date = request.GET.get('date')
        initial = {}
        if facility_id:
            try:
                selected_facility = Facility.objects.get(pk=facility_id)
                initial['facility'] = selected_facility
            except (ValueError, Facility.DoesNotExist):
                pass
        if selected_date:
            initial['booking_date'] = selected_date
        if selected_facility and selected_date:
            booked_slots = list(
                Booking.objects.filter(
                    facility=selected_facility,
                    booking_date=selected_date,
                )
                .exclude(status='CANCELLED')
                .values_list('time_slot', flat=True)
            )
        form = BookingForm(initial=initial)
    
    return render(request, 'facilities/create_booking.html', {
        'form': form,
        'time_slots': time_slots,
        'time_slot_values': time_slot_values,
        'booked_slots': booked_slots,
        'selected_date': selected_date,
    })

@login_required
def my_bookings_view(request):
    if request.user.is_resident:
        bookings = Booking.objects.filter(resident=request.user.resident).order_by('-booking_date')
    else:
        bookings = Booking.objects.all().order_by('-booking_date')
    return render(request, 'facilities/my_bookings.html', {'bookings': bookings})

# Staff confirms a booking
@login_required
def confirm_booking_view(request, pk):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    booking = get_object_or_404(Booking, pk=pk)
    booking.status = 'CONFIRMED'
    booking.save()
    return redirect('all_bookings')

# Staff or Resident cancels a booking
@login_required
def cancel_booking_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    
    # Only staff or the owner can cancel
    if request.user.is_staff_member or (request.user.is_resident and booking.resident == request.user.resident):
        booking.status = 'CANCELLED'
        booking.save()
    
    if request.user.is_staff_member:
        return redirect('all_bookings')
    return redirect('my_bookings')

# Staff views all bookings
@login_required
def all_bookings_view(request):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    bookings = Booking.objects.all().order_by('-created_at')
    return render(request, 'facilities/all_bookings.html', {'bookings': bookings})

# Staff toggles facility open/close status
@login_required
def toggle_facility_view(request, pk):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    facility = get_object_or_404(Facility, pk=pk)
    facility.is_open = not facility.is_open
    facility.save()
    
    # If closing facility, cancel all pending bookings for today and future
    if not facility.is_open:
        from django.utils import timezone
        today = timezone.localdate()
        bookings_to_cancel = Booking.objects.filter(
            facility=facility,
            booking_date__gte=today,
            status__in=['PENDING', 'CONFIRMED']
        )
        bookings_to_cancel.update(status='CANCELLED')
    
    return redirect('facility_list')

# Staff creates new facility
@login_required
def create_facility_view(request):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = FacilityForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('facility_list')
    else:
        form = FacilityForm()
    
    return render(request, 'facilities/create_facility.html', {'form': form})
