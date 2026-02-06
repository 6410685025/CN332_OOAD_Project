from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Facility, Booking
from .forms import BookingForm

@login_required
def facility_list_view(request):
    facilities = Facility.objects.all()
    my_bookings = []
    if request.user.is_resident:
        my_bookings = list(Booking.objects.filter(
            resident=request.user.resident
        ).exclude(status='CANCELLED').select_related('facility').order_by('booking_date')[:5])
    return render(request, 'facilities/facility_list.html', {
        'facilities': facilities,
        'my_bookings': my_bookings,
        'is_resident': request.user.is_resident,
    })

@login_required
def create_booking_view(request):
    if not request.user.is_resident:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.resident = request.user.resident
            booking.save()
            return redirect('my_bookings')
    else:
        facility_id = request.GET.get('facility')
        initial = {}
        if facility_id:
            try:
                initial['facility'] = Facility.objects.get(pk=facility_id)
            except (ValueError, Facility.DoesNotExist):
                pass
        form = BookingForm(initial=initial)
    
    return render(request, 'facilities/create_booking.html', {'form': form})

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
