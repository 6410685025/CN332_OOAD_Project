from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from facilities.models import Booking
from users.services.line_messaging import send_line_flex_message


class Command(BaseCommand):
    help = 'Send booking confirmation reminders and expire unconfirmed bookings.'

    def handle(self, *args, **options):
        now = timezone.now()
        self._expire_pending_bookings(now)
        self._send_confirmation_reminders(now)

    def _expire_pending_bookings(self, now):
        pending_bookings = Booking.objects.filter(status='PENDING')
        for booking in pending_bookings:
            start_dt, _ = booking.get_start_end_datetimes()
            if booking.confirmation_deadline and now > booking.confirmation_deadline:
                booking.status = 'EXPIRED'
                booking.save(update_fields=['status'])
                continue

            if now >= start_dt:
                booking.status = 'EXPIRED'
                booking.save(update_fields=['status'])

    def _send_confirmation_reminders(self, now):
        if not settings.APP_BASE_URL:
            return

        pending_bookings = Booking.objects.filter(status='PENDING', reminder_sent_at__isnull=True)
        for booking in pending_bookings:
            start_dt, _ = booking.get_start_end_datetimes()
            remind_at = start_dt - timedelta(hours=1)
            if now < remind_at:
                continue

            resident_user = booking.resident.user
            if not resident_user.line_user_id:
                booking.reminder_sent_at = now
                booking.confirmation_deadline = now + timedelta(minutes=15)
                booking.save(update_fields=['reminder_sent_at', 'confirmation_deadline'])
                continue

            booking.confirmation_deadline = now + timedelta(minutes=15)
            booking.reminder_sent_at = now
            booking.save(update_fields=['confirmation_deadline', 'reminder_sent_at'])

            details_url = f"{settings.APP_BASE_URL}/facilities/booking/{booking.pk}/"
            confirm_url = f"{settings.APP_BASE_URL}/facilities/booking/{booking.pk}/confirm/"
            date_label = booking.booking_date.strftime('%b %d, %Y')
            time_label = booking.time_slot

            bubble = {
                'type': 'bubble',
                'header': {
                    'type': 'box',
                    'layout': 'horizontal',
                    'backgroundColor': '#3b82f6',
                    'paddingAll': '12px',
                    'contents': [
                        {
                            'type': 'text',
                            'text': 'Booking Confirmation',
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
                            'type': 'box',
                            'layout': 'vertical',
                            'contents': [
                                {'type': 'text', 'text': 'Facility', 'size': 'sm', 'color': '#64748b'},
                                {'type': 'text', 'text': booking.facility.name, 'weight': 'bold', 'size': 'md'},
                            ],
                        },
                        {
                            'type': 'box',
                            'layout': 'horizontal',
                            'spacing': 'md',
                            'contents': [
                                {
                                    'type': 'box',
                                    'layout': 'vertical',
                                    'contents': [
                                        {'type': 'text', 'text': 'Date', 'size': 'sm', 'color': '#64748b'},
                                        {'type': 'text', 'text': date_label, 'weight': 'bold', 'size': 'md'},
                                    ],
                                },
                                {
                                    'type': 'box',
                                    'layout': 'vertical',
                                    'contents': [
                                        {'type': 'text', 'text': 'Time', 'size': 'sm', 'color': '#64748b'},
                                        {'type': 'text', 'text': time_label, 'weight': 'bold', 'size': 'md'},
                                    ],
                                },
                            ],
                        },
                    ],
                },
                'footer': {
                    'type': 'box',
                    'layout': 'vertical',
                    'spacing': 'sm',
                    'contents': [
                        {
                            'type': 'button',
                            'style': 'primary',
                            'color': '#22c55e',
                            'action': {
                                'type': 'uri',
                                'label': 'Confirm Booking',
                                'uri': confirm_url,
                            },
                        },
                        {
                            'type': 'button',
                            'style': 'secondary',
                            'action': {
                                'type': 'uri',
                                'label': 'View Details',
                                'uri': details_url,
                            },
                        },
                    ],
                },
            }

            try:
                send_line_flex_message(resident_user.line_user_id, 'Booking confirmation required', bubble)
            except Exception:
                pass
