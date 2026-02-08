from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
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


@login_required
@require_http_methods(["GET", "POST", "DELETE"])
def edit_announcement_view(request, pk):
    if not request.user.is_staff_member:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    announcement = get_object_or_404(Announcement, pk=pk)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            announcement = form.save()
            
            # Handle new file attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                if file:
                    AnnouncementAttachment.objects.create(
                        announcement=announcement,
                        file=file
                    )
            
            return JsonResponse({
                'success': True,
                'message': 'Announcement updated successfully',
                'announcement': {
                    'id': announcement.id,
                    'title': announcement.title,
                    'content': announcement.content,
                    'category': announcement.category,
                    'category_display': announcement.get_category_display(),
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
    # GET request - return announcement data
    attachments = []
    for att in announcement.attachments.all():
        attachments.append({
            'id': att.id,
            'name': att.file.name.split('/')[-1],
            'url': att.file.url
        })
    
    return JsonResponse({
        'success': True,
        'announcement': {
            'id': announcement.id,
            'title': announcement.title,
            'content': announcement.content,
            'category': announcement.category,
        },
        'attachments': attachments
    })


@login_required
@require_http_methods(["DELETE"])
def delete_attachment_view(request, pk):
    if not request.user.is_staff_member:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    attachment = get_object_or_404(AnnouncementAttachment, pk=pk)
    attachment.file.delete()
    attachment.delete()
    
    return JsonResponse({'success': True, 'message': 'Attachment deleted'})
