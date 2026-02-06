from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import LostFound
from .forms import LostFoundForm

@login_required
def lost_found_list_view(request):
    items = LostFound.objects.all().order_by('-reported_at')
    return render(request, 'lost_found/lost_found_list.html', {'items': items})

@login_required
def report_item_view(request):
    if not request.user.is_resident:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LostFoundForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.reporter = request.user.resident
            item.save()
            return redirect('lost_found_list')
    else:
        form = LostFoundForm()
    
    return render(request, 'lost_found/report_item.html', {'form': form})

@login_required
def resolve_item_view(request, pk):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    item = get_object_or_404(LostFound, pk=pk)
    item.status = 'RESOLVED'
    item.resolver = request.user.staff
    item.save()
    return redirect('lost_found_list')
