from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Announcement, AnnouncementAttachment
from .forms import AnnouncementForm, AnnouncementAttachmentForm

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
            
            # Handle file attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                if file:
                    AnnouncementAttachment.objects.create(
                        announcement=announcement,
                        file=file
                    )
            
            return redirect('announcement_list')
    else:
        form = AnnouncementForm()
    
    return render(request, 'announcements/create_announcement.html', {'form': form})
