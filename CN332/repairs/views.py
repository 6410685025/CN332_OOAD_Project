from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
import json
from .models import RepairRequest, WorkLog, RepairImage
from .forms import RepairRequestForm, AssignTechnicianForm, AssignStaffForm, UpdateRepairStatusForm, UpdateComplaintStatusForm, RatingForm, RepairImageForm
from django.shortcuts import render, redirect
from django.utils import timezone

@login_required
def create_repair_view(request):
    if not (request.user.is_resident or request.user.is_staff_member):
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RepairRequestForm(request.POST)
        if form.is_valid():
            repair = form.save(commit=False)
            
            # Assign resident based on role
            if request.user.is_resident:
                repair.resident = request.user.resident
            elif request.user.is_staff_member:
                # Staff can create repair for themselves if they're also a resident,
                # otherwise assign to a specific resident (handled by form)
                pass
            
            repair.save()
            
            # Handle image uploads
            images_data_str = request.POST.get('images_data', '[]')
            try:
                images_data = json.loads(images_data_str)
            except json.JSONDecodeError:
                images_data = []
            
            # Process uploaded images
            if images_data:
                for img_data in images_data:
                    img_id = img_data.get('id')
                    img_type = img_data.get('type', 'BEFORE')
                    
                    # Get the file from POST
                    file_key = f'image_{img_id}'
                    if file_key in request.FILES:
                        image_file = request.FILES[file_key]
                        RepairImage.objects.create(
                            repair_request=repair,
                            image=image_file,
                            image_type=img_type,
                            uploaded_by=request.user
                        )
            
            return redirect('repair_list')
    else:
        form = RepairRequestForm()
    
    return render(request, 'repairs/create_repair.html', {'form': form})

@login_required
def repair_list_view(request):
    user = request.user
    if user.is_resident:
        repairs = RepairRequest.objects.filter(resident=user.resident)
    elif user.is_staff_member:
        repairs = RepairRequest.objects.all()
    elif user.is_technician:
        repairs = RepairRequest.objects.filter(technician=user.technician)
    else:
        repairs = RepairRequest.objects.none()
    q = request.GET.get('q', '').strip()
    if q:
        if q.isdigit():
            repairs = repairs.filter(id=int(q))
        else:
            repairs = repairs.filter(
                Q(location__icontains=q) | Q(request_type__icontains=q) | Q(description__icontains=q)
            )
    repairs = repairs.select_related('technician__user', 'resident').order_by('-created_at')
    return render(request, 'repairs/repair_list.html', {'repairs': repairs, 'user': user})

@login_required
def repair_detail_view(request, pk):
    repair = get_object_or_404(RepairRequest, pk=pk)
    logs = repair.logs.all().order_by('-timestamp')
    
    # Handle complaint status update by staff
    complaint_form = None
    if (request.user.is_staff_member and 
        repair.request_type == 'COMPLAINT' and 
        repair.assigned_staff and 
        repair.assigned_staff.user == request.user and 
        repair.status != 'COMPLETED'):
        
        if request.method == 'POST':
            complaint_form = UpdateComplaintStatusForm(request.POST, instance=repair)
            if complaint_form.is_valid():
                complaint_form.save()
                work_note = complaint_form.cleaned_data.get('work_note')
                if work_note:
                    WorkLog.objects.create(
                        repair_request=repair,
                        description=work_note
                    )
                WorkLog.objects.create(
                    repair_request=repair,
                    description=f"Status updated to: {repair.get_status_display()}"
                )
                return redirect('repair_detail', pk=pk)
        else:
            complaint_form = UpdateComplaintStatusForm(instance=repair)
    
    return render(request, 'repairs/repair_detail.html', {
        'repair': repair, 
        'logs': logs,
        'complaint_form': complaint_form
    })

# Staff assigns technician or staff to repair
@login_required
def assign_technician_view(request, pk):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    repair = get_object_or_404(RepairRequest, pk=pk)
    
    # Use different form based on request type
    if repair.request_type == 'MAINTENANCE':
        FormClass = AssignTechnicianForm
        field_name = 'technician'
    else:  # COMPLAINT
        FormClass = AssignStaffForm
        field_name = 'assigned_staff'
    
    if request.method == 'POST':
        form = FormClass(request.POST, instance=repair)
        if form.is_valid():
            form.save()
            if repair.request_type == 'MAINTENANCE':
                WorkLog.objects.create(
                    repair_request=repair,
                    description=f"Assigned to technician: {repair.technician.user.username}"
                )
            else:
                WorkLog.objects.create(
                    repair_request=repair,
                    description=f"Assigned to staff: {repair.assigned_staff.user.username}"
                )
            return redirect('repair_list')
    else:
        form = FormClass(instance=repair)
    
    return render(request, 'repairs/assign_technician.html', {
        'form': form, 
        'repair': repair,
        'is_complaint': repair.request_type == 'COMPLAINT'
    })

# Technician updates repair status
@login_required
def update_repair_status_view(request, pk):
    if not request.user.is_technician:
        return redirect('dashboard')
    
    repair = get_object_or_404(RepairRequest, pk=pk, technician=request.user.technician)
    
    if request.method == 'POST':
        form = UpdateRepairStatusForm(request.POST, instance=repair)
        if form.is_valid():
            form.save()
            WorkLog.objects.create(
                repair_request=repair,
                description=f"Status updated to: {repair.get_status_display()}"
            )
            return redirect('repair_list')
    else:
        form = UpdateRepairStatusForm(instance=repair)
    
    return render(request, 'repairs/update_status.html', {'form': form, 'repair': repair})

# Resident rates completed repair
@login_required
def rate_repair_view(request, pk):
    if not request.user.is_resident:
        return redirect('dashboard')
    
    repair = get_object_or_404(RepairRequest, pk=pk, resident=request.user.resident, status='COMPLETED')
    
    if repair.rating:
        return redirect('repair_list')  # Already rated
    
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            repair.rating = int(form.cleaned_data['rating'])
            repair.save()
            return redirect('repair_list')
    else:
        form = RatingForm()
    
    return render(request, 'repairs/rate_repair.html', {'form': form, 'repair': repair})


@login_required
def technician_work_history_view(request):
    if not request.user.is_technician:
        return redirect('dashboard')

    tech = request.user.technician

    # base queryset: งานที่เสร็จแล้วของช่างคนนี้
    qs = RepairRequest.objects.filter(
        technician=tech,
        status='COMPLETED'
    ).select_related('resident', 'technician__user').order_by('-created_at')

    # -----------------------
    # Filters (เหมือนใน UI)
    # -----------------------
    q = request.GET.get('q', '').strip()
    date_range = request.GET.get('date_range', '30')   # 30 / 90 / all
    repair_type = request.GET.get('repair_type', 'ALL')  # ALL / MAINTENANCE / COMPLAINT
    rating = request.GET.get('rating', 'ALL')  # ALL / 5 / 4 / 3 / 2 / 1

    if q:
        # รองรับค้นหา id หรือ keyword
        if q.isdigit():
            qs = qs.filter(id=int(q))
        else:
            qs = qs.filter(
                Q(location__icontains=q) |
                Q(description__icontains=q) |
                Q(request_type__icontains=q)
            )

    if date_range != 'all':
        days = int(date_range)
        since = timezone.now() - timezone.timedelta(days=days)
        qs = qs.filter(created_at__gte=since)

    if repair_type != 'ALL':
        qs = qs.filter(request_type=repair_type)

    if rating != 'ALL':
        qs = qs.filter(rating=int(rating))

    # -----------------------
    # Stats cards
    # -----------------------
    total_completed = RepairRequest.objects.filter(technician=tech, status='COMPLETED').count()

    avg_rating = (
        RepairRequest.objects.filter(technician=tech, status='COMPLETED', rating__isnull=False)
        .aggregate(avg=Avg('rating'))['avg']
    ) or 0.0

    now = timezone.localtime(timezone.now())
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_count = RepairRequest.objects.filter(
        technician=tech, status='COMPLETED', created_at__gte=month_start
    ).count()

    context = {
        'repairs': qs,
        'total_completed': total_completed,
        'avg_rating': round(float(avg_rating), 1),
        'this_month_count': this_month_count,

        # keep filters selected
        'q': q,
        'date_range': date_range,
        'repair_type': repair_type,
        'rating_filter': rating,
    }
    return render(request, 'repairs/technician_work_history.html', context)
