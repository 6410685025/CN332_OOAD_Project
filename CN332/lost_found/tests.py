from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import LostFound
from .forms import LostFoundForm
from users.models import User, Resident, Staff

class LostFoundSetup(TestCase):
    def setUp(self):
        # 1. สร้าง User ที่เป็น Resident (ลูกบ้าน)
        self.resident_user = User.objects.create_user(
            username='resident1', 
            password='password123'
        )
        self.resident_profile = Resident.objects.create(user=self.resident_user)

        # 2. สร้าง User ที่เป็น Staff (นิติบุคคล)
        self.staff_user = User.objects.create_user(
            username='staff1', 
            password='password123'
        )
        self.staff_profile = Staff.objects.create(user=self.staff_user)

        # 3. สร้างของที่หาย/เจอ แบบที่ได้รับการอนุมัติแล้ว (Approved)
        self.approved_item = LostFound.objects.create(
            reporter=self.resident_profile,
            item_name='Black Wallet',
            description='Found near the pool.',
            location='Swimming Pool',
            item_type='FOUND',
            status='PENDING',
            is_approved=True
        )

        # 4. สร้างของที่หาย/เจอ แบบที่ยังไม่ได้รับการอนุมัติ (Not Approved)
        self.pending_item = LostFound.objects.create(
            reporter=self.resident_profile,
            item_name='House Keys',
            description='Lost my keys.',
            location='Gym',
            item_type='LOST',
            status='PENDING',
            is_approved=False
        )

class LostFoundModelTest(LostFoundSetup):
    def test_lost_found_str(self):
        """ทดสอบฟังก์ชัน __str__ ของโมเดล LostFound"""
        expected_str = 'Black Wallet (FOUND - PENDING)'
        self.assertEqual(str(self.approved_item), expected_str)

class LostFoundFormTest(TestCase):
    def test_valid_lost_found_form(self):
        """ทดสอบฟอร์มสร้างรายการ LostFound ด้วยข้อมูลที่ถูกต้อง"""
        data = {
            'item_type': 'LOST',
            'item_name': 'Cat',
            'description': 'White cat with a blue collar.',
            'location': 'Lobby'
        }
        form = LostFoundForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_lost_found_form(self):
        """ทดสอบฟอร์มสร้างรายการ LostFound เมื่อข้อมูลไม่ครบ (ขาดชื่อของ)"""
        data = {
            'item_type': 'LOST',
            'description': 'White cat with a blue collar.',
            'location': 'Lobby'
        }
        form = LostFoundForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('item_name', form.errors)

class LostFoundResidentViewTest(LostFoundSetup):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.login(username='resident1', password='password123')

    def test_list_view_resident(self):
        """ทดสอบ Resident เห็นเฉพาะรายการที่ is_approved=True เท่านั้น"""
        response = self.client.get(reverse('lost_found_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Black Wallet') # ควรเห็นชิ้นที่ Approve แล้ว
        self.assertNotContains(response, 'House Keys') # ไม่ควรเห็นชิ้นที่ยังไม่ Approve

    def test_report_item_view_get(self):
        """ทดสอบ Resident เข้าหน้าแจ้งของหาย (GET Request)"""
        response = self.client.get(reverse('report_item'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'lost_found/report_item.html')

    def test_report_item_view_post(self):
        """ทดสอบ Resident ส่งฟอร์มแจ้งของหาย (POST Request)"""
        data = {
            'item_type': 'LOST',
            'item_name': 'Earbuds',
            'description': 'White AirPods',
            'location': 'Garden'
        }
        response = self.client.post(reverse('report_item'), data)
        self.assertRedirects(response, reverse('lost_found_list'))
        self.assertEqual(LostFound.objects.count(), 3) # มี 2 อันจาก Setup + 1 อันที่เพิ่งสร้าง
        
        # ตรวจสอบว่าระบบบันทึกว่า Resident คนนี้เป็นคนแจ้ง (Reporter)
        new_item = LostFound.objects.order_by('-id').first()
        self.assertEqual(new_item.reporter, self.resident_profile)
        self.assertFalse(new_item.is_approved) # ของใหม่ต้องรออนุมัติ

    def test_claim_item_success(self):
        """ทดสอบ Resident กดแสดงความเป็นเจ้าของ (Claim)"""
        response = self.client.post(reverse('claim_item', args=[self.approved_item.pk]))
        self.assertRedirects(response, reverse('lost_found_list'))
        
        self.approved_item.refresh_from_db()
        self.assertEqual(self.approved_item.status, 'CLAIMED')
        self.assertEqual(self.approved_item.claimant, self.resident_profile)
        self.assertIsNotNone(self.approved_item.claimed_at)

    def test_resident_access_staff_views(self):
        """ทดสอบลูกบ้านแอบเข้าหน้าของ Staff (ต้องโดนเด้งกลับ)"""
        self.assertRedirects(self.client.post(reverse('resolve_item', args=[self.approved_item.pk])), reverse('dashboard'), fetch_redirect_response=False)
        self.assertRedirects(self.client.post(reverse('approve_item', args=[self.pending_item.pk])), reverse('dashboard'), fetch_redirect_response=False)

class LostFoundStaffViewTest(LostFoundSetup):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.login(username='staff1', password='password123')

    def test_list_view_staff(self):
        """ทดสอบ Staff ดูหน้ารายการ (ต้องเห็นของทั้งหมดรวมถึงที่ยังไม่ Approve)"""
        response = self.client.get(reverse('lost_found_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Black Wallet')
        self.assertContains(response, 'House Keys')

    def test_approve_item_success(self):
        """ทดสอบ Staff กดอนุมัติการแจ้งของหาย"""
        self.assertFalse(self.pending_item.is_approved)
        response = self.client.post(reverse('approve_item', args=[self.pending_item.pk]))
        self.assertRedirects(response, reverse('lost_found_list'))
        
        self.pending_item.refresh_from_db()
        self.assertTrue(self.pending_item.is_approved)

    def test_resolve_item_success(self):
        """ทดสอบ Staff กดปิดเคสของหาย (Resolved)"""
        response = self.client.post(reverse('resolve_item', args=[self.approved_item.pk]))
        self.assertRedirects(response, reverse('lost_found_list'))
        
        self.approved_item.refresh_from_db()
        self.assertEqual(self.approved_item.status, 'RESOLVED')
        self.assertEqual(self.approved_item.resolver, self.staff_profile)

    def test_resolved_item_hides_mark_resolved_button(self):
        """ทดสอบว่า item ที่ resolved แล้วไม่แสดงปุ่ม Mark Resolved"""
        self.approved_item.status = 'RESOLVED'
        self.approved_item.save()

        response = self.client.get(reverse('lost_found_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resolved')
        self.assertNotContains(response, 'Mark Resolved')

    def test_staff_access_resident_views(self):
        """ทดสอบ Staff แอบเข้าหน้าทำรายการของลูกบ้าน (ต้องโดนเด้งกลับ)"""
        self.assertRedirects(self.client.get(reverse('report_item')), reverse('dashboard'), fetch_redirect_response=False)
        self.assertRedirects(self.client.post(reverse('claim_item', args=[self.approved_item.pk])), reverse('dashboard'), fetch_redirect_response=False)