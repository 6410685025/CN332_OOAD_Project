from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Case, When, IntegerField
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import timedelta
from django.db import transaction

from users.models import Resident, User
from users.forms import ResidentCreationForm, ResidentProfileForm, ResidentPasswordChangeForm
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
        'upcoming_bookings_count': Booking.objects.filter(resident=resident, booking_date__gte=today, status__in=['PENDING', 'CONFIRMED']).count(),
        'announcements_count': Announcement.objects.filter(publish_date__gte=timezone.now() - timedelta(days=7)).count(),
        'recent_repairs': RepairRequest.objects.filter(resident=resident).order_by('-created_at')[:5],
        'recent_announcements': Announcement.objects.select_related('author').order_by('-publish_date')[:4],
        'resident_packages': Package.objects.filter(resident=resident).order_by(
            Case(
                When(status='RECEIVED', then=0),
                When(status='PICKED_UP', then=1),
                default=2,
                output_field=IntegerField()
            ),
            '-arrived_at'
        )[:5],
        'upcoming_bookings': Booking.objects.filter(resident=resident, booking_date__gte=today, status__in=['PENDING', 'CONFIRMED']).select_related('facility').order_by('booking_date')[:5],
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
@require_http_methods(["POST"])
def create_resident_view(request):
    if not request.user.is_staff_member:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    form = ResidentCreationForm(request.POST)
    
    if form.is_valid():
        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password'],
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'],
                    contact_number=form.cleaned_data.get('contact_number', ''),
                    is_resident=True
                )
                
                # Create resident
                resident = Resident.objects.create(
                    user=user,
                    building=form.cleaned_data['building'],
                    floor=form.cleaned_data['floor'],
                    room_number=form.cleaned_data['room_number']
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Resident created successfully',
                    'resident': {
                        'id': resident.id,
                        'user': {
                            'first_name': user.first_name,
                            'last_name': user.last_name,
                            'username': user.username,
                            'email': user.email,
                            'contact_number': user.contact_number
                        },
                        'building': resident.building,
                        'floor': resident.floor,
                        'room_number': resident.room_number
                    }
                })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        errors = form.errors.as_json()
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
def settings_view(request):
    return render(request, 'users/settings.html')


@login_required
@require_http_methods(["POST"])
def update_profile_view(request):
    if not request.user.is_resident:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    form = ResidentProfileForm(request.POST, request.FILES, instance=request.user)
    
    if form.is_valid():
        try:
            user = form.save(commit=False)
            
            # Handle profile photo
            if 'profile_photo' in request.FILES:
                user.profile_photo = request.FILES['profile_photo']
            
            user.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Profile updated successfully',
                'user': {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'contact_number': user.contact_number,
                    'profile_photo_url': user.profile_photo.url if user.profile_photo else None
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)


@login_required
@require_http_methods(["POST"])
def change_password_view(request):
    if not request.user.is_resident:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    form = ResidentPasswordChangeForm(request.user, request.POST)
    
    if form.is_valid():
        try:
            user = form.save()
            return JsonResponse({
                'success': True,
                'message': 'Password changed successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
