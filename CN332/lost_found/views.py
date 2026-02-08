from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from .models import LostFound
from .forms import LostFoundForm

@login_required
def lost_found_list_view(request):
    # Staff sees all items, residents see only approved items
    if request.user.is_staff_member:
        items_list = LostFound.objects.all().order_by('-reported_at')
    else:
        items_list = LostFound.objects.filter(is_approved=True).order_by('-reported_at')
    
    # Calculate stats (based on filtered list)
    total_items = items_list.count()
    review_pending = items_list.filter(status='PENDING').count()
    resolved_count = items_list.filter(status='RESOLVED').count()
    
    # Paginate items - 10 per page for staff, 12 per page for residents (grid layout)
    items_per_page = 10 if request.user.is_staff_member else 12
    paginator = Paginator(items_list, items_per_page)
    page_number = request.GET.get('page', 1)
    items = paginator.get_page(page_number)
    
    context = {
        'items': items,
        'total_items': total_items,
        'review_pending': review_pending,
        'resolved_count': resolved_count,
    }
    
    return render(request, 'lost_found/lost_found_list.html', context)

@login_required
def report_item_view(request):
    if not request.user.is_resident:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LostFoundForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.reporter = request.user.resident
            item.save()
            return redirect('lost_found_list')
    else:
        form = LostFoundForm()
    
    return render(request, 'lost_found/report_item.html', {'form': form})

@login_required
def claim_item_view(request, pk):
    if not request.user.is_resident:
        return redirect('dashboard')

    item = get_object_or_404(LostFound, pk=pk)
    if item.status == 'PENDING':
        item.status = 'CLAIMED'
        item.claimant = request.user.resident
        item.claimed_at = timezone.now()
        item.save()
    return redirect('lost_found_list')


@login_required
def resolve_item_view(request, pk):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    item = get_object_or_404(LostFound, pk=pk)
    item.status = 'RESOLVED'
    item.resolver = request.user.staff
    item.save()
    return redirect('lost_found_list')

@login_required
def approve_item_view(request, pk):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    item = get_object_or_404(LostFound, pk=pk)
    item.is_approved = True
    item.save()
    return redirect('lost_found_list')
