from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from .models import Announcement, AnnouncementAttachment
from .forms import AnnouncementForm
from users.models import User, Staff

class AnnouncementSetup(TestCase):
    def setUp(self):
        # สร้าง User ทั่วไป (ไม่ต้องเซ็ต is_staff_member แบบแมนนวลแล้ว)
        self.normal_user = User.objects.create_user(
            username='normaluser', 
            password='password123',
            line_user_id='U1234567890'
        )

        # สร้าง User ที่เป็น Staff
        self.staff_user = User.objects.create_user(
            username='staffuser', 
            password='password123'
        )
        
        # การสร้างข้อมูล Staff ผูกกับ staff_user จะทำให้ Property is_staff_member เป็น True อัตโนมัติ
        self.staff_profile = Staff.objects.create(user=self.staff_user)

        # สร้าง Announcement เริ่มต้นสำหรับการทดสอบ
        self.announcement = Announcement.objects.create(
            title='Test Announcement',
            content='This is a test content.',
            category='GENERAL',
            author=self.staff_profile
        )

class AnnouncementModelTest(AnnouncementSetup):
    def test_announcement_str(self):
        """ทดสอบการคืนค่า __str__ ของ Announcement model"""
        self.assertEqual(str(self.announcement), 'Test Announcement')

    def test_attachment_str(self):
        """ทดสอบการคืนค่า __str__ ของ AnnouncementAttachment model"""
        mock_file = SimpleUploadedFile("test_file.pdf", b"file_content", content_type="application/pdf")
        attachment = AnnouncementAttachment.objects.create(
            announcement=self.announcement,
            file=mock_file
        )
        self.assertEqual(str(attachment), 'Attachment for Test Announcement')

class AnnouncementFormTest(TestCase):
    def test_valid_announcement_form(self):
        """ทดสอบฟอร์มเมื่อใส่ข้อมูลที่ถูกต้อง"""
        data = {
            'title': 'New Event',
            'category': 'EVENTS',
            'content': 'Join us for the new event!'
        }
        form = AnnouncementForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_announcement_form(self):
        """ทดสอบฟอร์มเมื่อข้อมูลไม่ครบถ้วน (ไม่มี title)"""
        data = {
            'category': 'EVENTS',
            'content': 'Join us for the new event!'
        }
        form = AnnouncementForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

class AnnouncementViewTest(AnnouncementSetup):
    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_announcement_list_view_authenticated(self):
        """ทดสอบการเข้าถึงหน้ารวมประกาศเมื่อล็อกอินแล้ว"""
        self.client.login(username='normaluser', password='password123')
        response = self.client.get(reverse('announcement_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcements/announcement_list.html')
        self.assertContains(response, 'Test Announcement')

    def test_announcement_detail_view(self):
        """ทดสอบการเข้าถึงหน้าดูรายละเอียดประกาศ"""
        self.client.login(username='normaluser', password='password123')
        response = self.client.get(reverse('announcement_detail', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcements/announcement_detail.html')
        self.assertContains(response, 'Test Announcement')
        self.assertContains(response, 'This is a test content.')

    def test_create_announcement_view_non_staff(self):
        """ทดสอบว่า User ธรรมดาไม่สามารถเข้าหน้าสร้างประกาศได้"""
        self.client.login(username='normaluser', password='password123')
        response = self.client.get(reverse('create_announcement'))
        # ควรถูก redirect กลับไปที่ dashboard ตามโค้ดใน views.py
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)

    @patch('announcements.views.send_line_flex_message')
    def test_create_announcement_view_staff_post(self, mock_send_line):
        """ทดสอบการสร้างประกาศใหม่โดย Staff และจำลองการส่ง LINE"""
        self.client.login(username='staffuser', password='password123')
        data = {
            'title': 'Emergency Alert',
            'category': 'EMERGENCY',
            'content': 'Water supply will be cut off.',
        }
        response = self.client.post(reverse('create_announcement'), data)
        
        # ตรวจสอบว่าหลังจากสร้างเสร็จจะต้อง Redirect กลับไปหน้า list
        self.assertRedirects(response, reverse('announcement_list'))
        
        # ตรวจสอบว่าประกาศถูกสร้างลงฐานข้อมูลจริงๆ
        self.assertEqual(Announcement.objects.count(), 2)
        new_announcement = Announcement.objects.last()
        self.assertEqual(new_announcement.title, 'Emergency Alert')
        self.assertEqual(new_announcement.author, self.staff_profile)
        
        # ตรวจสอบว่าฟังก์ชันส่ง LINE ถูกเรียกใช้งาน
        mock_send_line.assert_called()

    def test_edit_announcement_unauthorized(self):
        """ทดสอบการแก้ไขประกาศโดย User ที่ไม่มีสิทธิ์"""
        self.client.login(username='normaluser', password='password123')
        response = self.client.post(reverse('edit_announcement', args=[self.announcement.pk]), {})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'Unauthorized')

    def test_edit_announcement_authorized_get(self):
        """ทดสอบการดึงข้อมูลประกาศเพื่อนำมาแก้ไข (GET request แบบ JSON)"""
        self.client.login(username='staffuser', password='password123')
        response = self.client.get(reverse('edit_announcement', args=[self.announcement.pk]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['announcement']['title'], 'Test Announcement')

    def test_delete_attachment_unauthorized(self):
        """ทดสอบการลบไฟล์แนบโดยผู้ไม่มีสิทธิ์"""
        self.client.login(username='normaluser', password='password123')
        # จำลองการสร้างไฟล์แนบ
        mock_file = SimpleUploadedFile("test.jpg", b"image", content_type="image/jpeg")
        attachment = AnnouncementAttachment.objects.create(announcement=self.announcement, file=mock_file)
        
        response = self.client.delete(reverse('delete_attachment', args=[attachment.pk]))
        self.assertEqual(response.status_code, 403)

    # ---------------- เทสต์เพิ่มเติมเพื่อเพิ่ม Coverage ---------------- #

    def test_create_announcement_view_staff_get(self):
        """ทดสอบการเปิดหน้าฟอร์มสร้างประกาศโดย Staff (GET Request)"""
        self.client.login(username='staffuser', password='password123')
        response = self.client.get(reverse('create_announcement'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'announcements/create_announcement.html')

    @patch('announcements.views.send_line_flex_message')
    def test_create_announcement_with_attachments(self, mock_send_line):
        """ทดสอบการสร้างประกาศพร้อมกับแนบไฟล์"""
        self.client.login(username='staffuser', password='password123')
        mock_file = SimpleUploadedFile("test_doc.pdf", b"file_content", content_type="application/pdf")
        data = {
            'title': 'Test with Attachment',
            'category': 'GENERAL',
            'content': 'Check out this file.',
            'attachments': [mock_file] # จำลองการอัปโหลดไฟล์
        }
        response = self.client.post(reverse('create_announcement'), data)
        self.assertRedirects(response, reverse('announcement_list'))
        # เช็กว่าไฟล์ถูกบันทึกลงฐานข้อมูลไหม
        self.assertEqual(AnnouncementAttachment.objects.count(), 1)

    def test_edit_announcement_authorized_post_success(self):
        """ทดสอบแก้ไขข้อมูลประกาศสำเร็จ (POST Request)"""
        self.client.login(username='staffuser', password='password123')
        data = {
            'title': 'Updated Title',
            'category': 'EVENTS',
            'content': 'Updated Content',
        }
        response = self.client.post(reverse('edit_announcement', args=[self.announcement.pk]), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        # รีเฟรชข้อมูลจากฐานข้อมูลเพื่อเช็กว่าเปลี่ยนจริง
        self.announcement.refresh_from_db()
        self.assertEqual(self.announcement.title, 'Updated Title')
        self.assertEqual(self.announcement.category, 'EVENTS')

    def test_edit_announcement_authorized_post_invalid(self):
        """ทดสอบแก้ไขข้อมูลประกาศแต่ใส่ข้อมูลไม่ครบ (ฟอร์มพัง)"""
        self.client.login(username='staffuser', password='password123')
        data = {
            'title': '', # ปล่อยชื่อประกาศว่างไว้เพื่อให้ Error
            'category': 'EVENTS',
            'content': 'Updated Content',
        }
        response = self.client.post(reverse('edit_announcement', args=[self.announcement.pk]), data)
        self.assertEqual(response.status_code, 400) # ควรคืนค่า 400 Bad Request
        self.assertFalse(response.json()['success'])
        self.assertIn('title', response.json()['errors'])

    def test_delete_attachment_authorized_success(self):
        """ทดสอบลบไฟล์แนบโดย Staff"""
        self.client.login(username='staffuser', password='password123')
        mock_file = SimpleUploadedFile("test.jpg", b"image", content_type="image/jpeg")
        attachment = AnnouncementAttachment.objects.create(announcement=self.announcement, file=mock_file)
        
        # ยิงคำสั่งลบไฟล์
        response = self.client.delete(reverse('delete_attachment', args=[attachment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        # ตรวจสอบว่าไฟล์หายไปจากฐานข้อมูลแล้ว
        self.assertEqual(AnnouncementAttachment.objects.count(), 0)
        
    @patch('announcements.views.send_line_flex_message', side_effect=Exception("LINE API Error"))
    def test_create_announcement_line_api_error(self, mock_send_line):
        """ทดสอบตอนสร้างประกาศแต่ระบบ LINE พัง (เช็ก Except block)"""
        self.client.login(username='staffuser', password='password123')
        data = {
            'title': 'Title',
            'category': 'GENERAL',
            'content': 'Content',
        }
        # โค้ดไม่ควรพัง แต่ควรทำงานต่อจนจบและ Redirect
        response = self.client.post(reverse('create_announcement'), data)
        self.assertRedirects(response, reverse('announcement_list'))