from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Announcement, AnnouncementAttachment
from .forms import AnnouncementForm, AnnouncementAttachmentForm
from users.models import User
from users.services.line_messaging import send_line_flex_message

@login_required
def announcement_list_view(request):
    announcements = Announcement.objects.all().order_by('-publish_date')
    return render(request, 'announcements/announcement_list.html', {'announcements': announcements})


@login_required
def announcement_detail_view(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    return render(request, 'announcements/announcement_detail.html', {'announcement': announcement})

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

            try:
                if settings.APP_BASE_URL:
                    detail_url = f"{settings.APP_BASE_URL}{reverse('announcement_detail', kwargs={'pk': announcement.pk})}"
                else:
                    detail_url = request.build_absolute_uri(
                        reverse('announcement_detail', kwargs={'pk': announcement.pk})
                    )

                header_title = 'Urgent Announcement' if announcement.category == 'EMERGENCY' else 'New Announcement'
                header_color = '#dc2626' if announcement.category == 'EMERGENCY' else '#ef4444'
                notice_text = 'Please store sufficient water in advance. We apologize for any inconvenience.'
                if announcement.category != 'MAINTENANCE':
                    notice_text = announcement.content.split('\n')[0][:120] if announcement.content else ''

                bubble = {
                    'type': 'bubble',
                    'header': {
                        'type': 'box',
                        'layout': 'horizontal',
                        'backgroundColor': header_color,
                        'paddingAll': '12px',
                        'contents': [
                            {
                                'type': 'text',
                                'text': header_title,
                                'weight': 'bold',
                                'color': '#ffffff',
                                'size': 'md',
                            }
                        ],
                    },
                    'body': {
                        'type': 'box',
                        'layout': 'vertical',
                        'spacing': 'md',
                        'contents': [
                            {
                                'type': 'text',
                                'text': announcement.title,
                                'weight': 'bold',
                                'size': 'md',
                                'wrap': True,
                            },
                            {
                                'type': 'text',
                                'text': announcement.content,
                                'size': 'sm',
                                'color': '#475569',
                                'wrap': True,
                            },
                            {
                                'type': 'box',
                                'layout': 'vertical',
                                'backgroundColor': '#fef2f2',
                                'cornerRadius': '10px',
                                'paddingAll': '10px',
                                'contents': [
                                    {
                                        'type': 'text',
                                        'text': notice_text,
                                        'size': 'sm',
                                        'color': '#b91c1c',
                                        'wrap': True,
                                    }
                                ],
                            },
                        ],
                    },
                    'footer': {
                        'type': 'box',
                        'layout': 'vertical',
                        'contents': [
                            {
                                'type': 'button',
                                'style': 'primary',
                                'color': header_color,
                                'action': {
                                    'type': 'uri',
                                    'label': 'Read Full Notice',
                                    'uri': detail_url,
                                },
                            }
                        ],
                    },
                }

                recipients = User.objects.filter(line_user_id__isnull=False).exclude(line_user_id='')
                for user in recipients:
                    try:
                        send_line_flex_message(user.line_user_id, announcement.title, bubble)
                    except Exception:
                        continue
            except Exception:
                messages.error(request, 'ส่งประกาศผ่าน LINE ไม่สำเร็จ')
            
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
