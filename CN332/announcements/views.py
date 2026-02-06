from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Announcement
from .forms import AnnouncementForm

@login_required
def announcement_list_view(request):
    announcements = Announcement.objects.all().order_by('-publish_date')
    return render(request, 'announcements/announcement_list.html', {'announcements': announcements})

@login_required
def create_announcement_view(request):
    if not request.user.is_staff_member:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user.staff
            announcement.save()
            return redirect('announcement_list')
    else:
        form = AnnouncementForm()
    
    return render(request, 'announcements/create_announcement.html', {'form': form})
