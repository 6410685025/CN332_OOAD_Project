from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta

from users.models import Resident
from repairs.models import RepairRequest
from packages.models import Package
from facilities.models import Booking
from announcements.models import Announcement
from lost_found.models import LostFound

def login_view(request):
    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    user = request.user
    if user.is_resident:
        return redirect('resident_dashboard')
    elif user.is_staff_member:
        return redirect('staff_dashboard')
    elif user.is_technician:
        return redirect('technician_dashboard')
    return render(request, 'dashboard_error.html')

@login_required
def resident_dashboard(request):
    user = request.user
    resident = user.resident
    today = timezone.now().date()
    
    context = {
        'pending_repairs': RepairRequest.objects.filter(resident=resident, status='PENDING').count(),
        'pending_packages': Package.objects.filter(resident=resident, status='RECEIVED').count(),
        'upcoming_bookings_count': Booking.objects.filter(resident=resident, booking_date__gte=today).count(),
        'announcements_count': Announcement.objects.filter(publish_date__gte=timezone.now() - timedelta(days=7)).count(),
        'recent_repairs': RepairRequest.objects.filter(resident=resident).order_by('-created_at')[:5],
        'recent_announcements': Announcement.objects.select_related('author').order_by('-publish_date')[:4],
        'resident_packages': Package.objects.filter(resident=resident).order_by('-arrived_at')[:5],
        'upcoming_bookings': Booking.objects.filter(resident=resident, booking_date__gte=today).select_related('facility').order_by('booking_date')[:5],
    }
    return render(request, 'resident/dashboard.html', context)

@login_required
def staff_dashboard(request):
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    context = {
        'pending_repairs': RepairRequest.objects.filter(status='PENDING').count(),
        'pending_packages': Package.objects.filter(status='RECEIVED').count(),
        'pending_bookings': Booking.objects.filter(status='PENDING').count(),
        'pending_lost_found': LostFound.objects.filter(status='PENDING').count(),
        'active_announcements': Announcement.objects.count(),
        'total_repairs': RepairRequest.objects.count(),
        'recent_repairs_today': RepairRequest.objects.filter(created_at__gte=today_start).count(),
        'packages_today': Package.objects.filter(status='RECEIVED', arrived_at__gte=today_start).count(),
        'recent_repairs': RepairRequest.objects.select_related('resident', 'technician').order_by('-created_at')[:5],
        'recent_packages': Package.objects.filter(status='RECEIVED').select_related('resident').order_by('-arrived_at')[:4],
    }
    return render(request, 'staff/dashboard.html', context)

@login_required
def technician_dashboard(request):
    user = request.user
    technician = user.technician
    
    repairs = RepairRequest.objects.filter(technician=technician).order_by('-created_at')
    
    context = {
        'assigned_jobs': repairs.exclude(status='COMPLETED').count(),
        'in_progress': repairs.filter(status='ON_PROCESS').count(),
        'completed_jobs': repairs.filter(status='COMPLETED').count(),
        'repairs': repairs[:10],
    }
    return render(request, 'technician/dashboard.html', context)


@login_required
def residents_list_view(request):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    residents = Resident.objects.select_related('user').order_by('building', 'floor', 'room_number')
    return render(request, 'users/residents_list.html', {'residents': residents})


@login_required
def settings_view(request):
    return render(request, 'users/settings.html')
