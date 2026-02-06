from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Package
from .forms import PackageForm

@login_required
def package_list_view(request):
    user = request.user
    if user.is_resident:
        packages = Package.objects.filter(resident=user.resident).order_by('-arrived_at')
    elif user.is_staff_member:
        packages = Package.objects.all().order_by('-arrived_at')
    else:
        packages = []
    return render(request, 'packages/package_list.html', {'packages': packages})

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
    return redirect('package_list')
