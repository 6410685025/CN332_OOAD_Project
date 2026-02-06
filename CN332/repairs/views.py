from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import RepairRequest, WorkLog
from .forms import RepairRequestForm, AssignTechnicianForm, UpdateRepairStatusForm, RatingForm

@login_required
def create_repair_view(request):
    if not request.user.is_resident:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RepairRequestForm(request.POST)
        if form.is_valid():
            repair = form.save(commit=False)
            repair.resident = request.user.resident
            repair.save()
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
    return render(request, 'repairs/repair_detail.html', {'repair': repair, 'logs': logs})

# Staff assigns technician to repair
@login_required
def assign_technician_view(request, pk):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    repair = get_object_or_404(RepairRequest, pk=pk)
    
    if request.method == 'POST':
        form = AssignTechnicianForm(request.POST, instance=repair)
        if form.is_valid():
            form.save()
            WorkLog.objects.create(
                repair_request=repair,
                description=f"Assigned to technician: {repair.technician.user.username}"
            )
            return redirect('repair_list')
    else:
        form = AssignTechnicianForm(instance=repair)
    
    return render(request, 'repairs/assign_technician.html', {'form': form, 'repair': repair})

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
