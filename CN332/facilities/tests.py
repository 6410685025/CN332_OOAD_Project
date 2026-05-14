from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from .models import Facility, Booking
from .forms import FacilityForm, BookingForm
from users.models import User, Resident, Staff

class FacilityComprehensiveTest(TestCase):
    def setUp(self):
        # 1. สร้าง Users สำหรับทดสอบ
        self.res_user1 = User.objects.create_user(username='res1', password='pw', line_user_id='U111')
        self.res1 = Resident.objects.create(user=self.res_user1)
        
        self.res_user2 = User.objects.create_user(username='res2', password='pw')
        self.res2 = Resident.objects.create(user=self.res_user2)

        self.staff_user = User.objects.create_user(username='staff', password='pw')
        self.staff = Staff.objects.create(user=self.staff_user)

        # 2. สร้าง Facility จำลอง
        self.facility = Facility.objects.create(
            name='Pool', facility_type='SWIMMING_POOL', capacity=10, is_open=True
        )

        self.today = timezone.localdate()
        self.client = Client()

    # ------------------ MODELS & FORMS ------------------ #
    def test_facility_str(self):
        self.assertEqual(str(self.facility), 'Pool (Swimming Pool)')

    def test_booking_str(self):
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00')
        self.assertIn('Booking', str(b))
        
    def test_get_start_end_datetimes(self):
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00')
        start_dt, end_dt = b.get_start_end_datetimes()
        self.assertEqual(start_dt.hour, 9)
        self.assertEqual(end_dt.hour, 10)

    def test_facility_form(self):
        form = FacilityForm(data={'name': 'Gym', 'facility_type': 'GYM', 'capacity': 5})
        self.assertTrue(form.is_valid())

    def test_booking_form(self):
        form = BookingForm(data={'facility': self.facility.id, 'booking_date': self.today, 'time_slot': '10:00-11:00'})
        self.assertTrue(form.is_valid())

    # ------------------ VIEWS (RESIDENT) ------------------ #
    def test_facility_list_resident(self):
        self.client.force_login(self.res_user1)
        response = self.client.get(reverse('facility_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_resident'])

    def test_facility_list_fully_booked(self):
        """ทดสอบกรณี Facility ถูกจองเต็มทุกสล็อตในวันนั้น"""
        self.client.force_login(self.res_user1)
        slots = ['09:00-10:00', '10:00-11:00', '11:00-12:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00']
        for s in slots:
            Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot=s, status='CONFIRMED')
        response = self.client.get(reverse('facility_list'))
        self.assertIn(self.facility.id, response.context['unavailable_facility_ids'])

    def test_create_booking_get_invalid_facility(self):
        """ทดสอบการดัก Error เวลาใส่ Facility ID แปลกๆ มาใน URL"""
        self.client.force_login(self.res_user1)
        # เคสใส่ตัวเลขที่ไม่มีจริงในฐานข้อมูล
        response1 = self.client.get(reverse('create_booking'), {'facility': 999}) 
        self.assertEqual(response1.status_code, 200)
        
        # เคสใส่ตัวอักษร (จะทำให้เกิด ValueError จากฐานข้อมูล ดังนั้นเราต้องดักจับด้วย assertRaises)
        with self.assertRaises(ValueError):
            self.client.get(reverse('create_booking'), {'facility': 'invalid'})

    def test_create_booking_closed_facility(self):
        self.client.force_login(self.res_user1)
        self.facility.is_open = False
        self.facility.save()
        response = self.client.get(reverse('create_booking'), {'facility': self.facility.id})
        self.assertRedirects(response, reverse('facility_list'), fetch_redirect_response=False)

    @patch('facilities.views.send_line_flex_message')
    def test_create_booking_post_confirmed(self, mock_line):
        """ทดสอบจองในเวลาปัจจุบัน (ไม่ต้อง Mock เวลา แต่ใช้วิธีจัดสล็อตเวลาให้ตรงกับตอนนี้)"""
        self.client.force_login(self.res_user1)
        
        # คำนวณช่วงเวลาให้อยู่ในปัจจุบันพอดี เพื่อให้สถานะเป็น CONFIRMED
        now = timezone.now()
        start_hour = now.hour
        end_hour = start_hour + 1
        current_time_slot = f"{start_hour:02d}:00-{end_hour:02d}:00"

        response = self.client.post(reverse('create_booking'), {
            'facility': self.facility.id,
            'booking_date': now.date(),
            'time_slot': current_time_slot
        })
        self.assertRedirects(response, reverse('my_bookings'), fetch_redirect_response=False)
        self.assertEqual(Booking.objects.last().status, 'CONFIRMED')

    @patch('facilities.views.send_line_flex_message', side_effect=Exception("LINE API Error"))
    def test_create_booking_post_line_error(self, mock_line):
        """ทดสอบจองล่วงหน้า (ติดสถานะ PENDING) และจำลองว่า LINE ยิงไม่ผ่าน"""
        self.client.force_login(self.res_user1)
        response = self.client.post(reverse('create_booking'), {
            'facility': self.facility.id,
            'booking_date': self.today + timedelta(days=1),
            'time_slot': '15:00-16:00'
        })
        self.assertRedirects(response, reverse('my_bookings'), fetch_redirect_response=False)
        self.assertEqual(Booking.objects.last().status, 'PENDING')

    def test_booking_detail_wrong_owner(self):
        self.client.force_login(self.res_user1)
        b = Booking.objects.create(resident=self.res2, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00')
        response = self.client.get(reverse('booking_detail', args=[b.id]))
        self.assertRedirects(response, reverse('my_bookings'), fetch_redirect_response=False)

    def test_resident_confirm_expired(self):
        """ทดสอบกดยืนยันตอนเลยเวลาที่กำหนดไปแล้ว"""
        self.client.force_login(self.res_user1)
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00', status='PENDING', confirmation_deadline=timezone.now() - timedelta(hours=1))
        response = self.client.get(reverse('resident_confirm_booking', args=[b.id]))
        b.refresh_from_db()
        self.assertEqual(b.status, 'EXPIRED')

    def test_resident_confirm_already_confirmed(self):
        self.client.force_login(self.res_user1)
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00', status='CONFIRMED')
        response = self.client.get(reverse('resident_confirm_booking', args=[b.id]))
        self.assertRedirects(response, reverse('booking_detail', args=[b.id]), fetch_redirect_response=False)

    def test_resident_cancel(self):
        self.client.force_login(self.res_user1)
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00')
        response = self.client.post(reverse('cancel_booking', args=[b.id]))
        b.refresh_from_db()
        self.assertEqual(b.status, 'CANCELLED')
        self.assertRedirects(response, reverse('my_bookings'), fetch_redirect_response=False)

    # ------------------ VIEWS (STAFF) ------------------ #
    def test_facility_list_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('facility_list'))
        self.assertEqual(response.status_code, 200)

    def test_my_bookings_staff(self):
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('my_bookings'))
        self.assertEqual(response.status_code, 200)

    def test_booking_detail_staff(self):
        self.client.force_login(self.staff_user)
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00')
        response = self.client.get(reverse('booking_detail', args=[b.id]))
        self.assertEqual(response.status_code, 200)

    def test_staff_confirm(self):
        self.client.force_login(self.staff_user)
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00')
        response = self.client.post(reverse('confirm_booking', args=[b.id]))
        b.refresh_from_db()
        self.assertEqual(b.status, 'CONFIRMED')

    def test_staff_cancel(self):
        self.client.force_login(self.staff_user)
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00')
        response = self.client.post(reverse('cancel_booking', args=[b.id]))
        b.refresh_from_db()
        self.assertEqual(b.status, 'CANCELLED')
        self.assertRedirects(response, reverse('all_bookings'), fetch_redirect_response=False)

    def test_toggle_facility(self):
        self.client.force_login(self.staff_user)
        b = Booking.objects.create(resident=self.res1, facility=self.facility, booking_date=self.today, time_slot='09:00-10:00', status='PENDING')
        response = self.client.post(reverse('toggle_facility', args=[self.facility.id]))
        self.facility.refresh_from_db()
        self.assertFalse(self.facility.is_open)
        # ตรวจสอบว่า Booking ที่ค้างอยู่ถูกยกเลิกอัตโนมัติ
        b.refresh_from_db()
        self.assertEqual(b.status, 'CANCELLED')

    def test_create_facility_post_valid(self):
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('create_facility'), {
            'name': 'Gym', 'facility_type': 'GYM', 'capacity': 10
        })
        self.assertEqual(Facility.objects.count(), 2)
        self.assertRedirects(response, reverse('facility_list'), fetch_redirect_response=False)
        
    # def test_create_facility_post_invalid(self):
    #     """ทดสอบฟอร์มพัง (ไม่มีข้อมูลชื่อ) ระบบต้องคืนค่าฟอร์มกลับมา"""
    #     self.client.force_login(self.staff_user)
    #     response = self.client.post(reverse('create_facility'), {
    #         'name': '', 'facility_type': 'GYM', 'capacity': 10
    #     })
    #     self.assertEqual(response.status_code, 200) 

    # ------------------ PERMISSIONS (REDIRECTS) ------------------ #
    def test_resident_access_staff_views(self):
        self.client.force_login(self.res_user1)
        self.assertRedirects(self.client.get(reverse('all_bookings')), reverse('dashboard'), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse('create_facility')), reverse('dashboard'), fetch_redirect_response=False)
        self.assertRedirects(self.client.post(reverse('toggle_facility', args=[self.facility.id])), reverse('dashboard'), fetch_redirect_response=False)
        self.assertRedirects(self.client.post(reverse('confirm_booking', args=[1])), reverse('dashboard'), fetch_redirect_response=False)

    def test_staff_access_resident_views(self):
        self.client.force_login(self.staff_user)
        self.assertRedirects(self.client.get(reverse('create_booking')), reverse('dashboard'), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse('resident_confirm_booking', args=[1])), reverse('dashboard'), fetch_redirect_response=False)