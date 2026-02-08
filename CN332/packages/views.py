from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Package
from .forms import PackageForm

@login_required
def package_list_view(request):
    user = request.user
    if user.is_resident:
        packages_list = Package.objects.filter(resident=user.resident).order_by('-arrived_at')
    elif user.is_staff_member:
        packages_list = Package.objects.all().order_by('-arrived_at')
    else:
        packages_list = Package.objects.none()
    
    # Calculate stats from all packages
    total_packages = packages_list.count()
    received_count = packages_list.filter(status='RECEIVED').count()
    picked_up_count = packages_list.exclude(status='RECEIVED').count()
    today = timezone.localtime().date()
    today_count = packages_list.filter(arrived_at__date=today).count()
    
    # Paginate packages - 12 per page for residents (grid), 20 per page for staff (table)
    items_per_page = 12 if user.is_resident else 20
    paginator = Paginator(packages_list, items_per_page)
    page_number = request.GET.get('page', 1)
    packages = paginator.get_page(page_number)
    
    context = {
        'packages': packages,
        'total_packages': total_packages,
        'received_count': received_count,
        'picked_up_count': picked_up_count,
        'today_count': today_count,
    }
    
    return render(request, 'packages/package_list.html', context)

@login_required
def receive_package_view(request):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PackageForm(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            package.handled_by = request.user.staff
            package.save()
            return redirect('package_list')
    else:
        form = PackageForm()
    
    return render(request, 'packages/receive_package.html', {'form': form})

@login_required
def mark_picked_up_view(request, pk):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    package = get_object_or_404(Package, pk=pk)
    package.status = 'PICKED_UP'
    package.picked_up_at = timezone.now()
    package.save()

@login_required
@require_http_methods(["POST"])
def receive_package_resident_view(request, pk):
    """Allow resident to mark their own package as picked up"""
    if not request.user.is_resident:
        return JsonResponse({'error': 'Only residents can use this endpoint'}, status=403)
    
    try:
        package = Package.objects.get(pk=pk, resident=request.user.resident)
        package.status = 'PICKED_UP'
        package.picked_up_at = timezone.now()
        package.save()
        return JsonResponse({'success': True, 'message': 'Package marked as picked up'})
    except Package.DoesNotExist:
        return JsonResponse({'error': 'Package not found'}, status=404)
    return redirect('package_list')
