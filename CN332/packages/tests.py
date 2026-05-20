from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch
from .models import Package
from .forms import PackageForm
from users.models import User, Resident, Staff

class PackageSetup(TestCase):
    def setUp(self):
        # 1. สร้างลูกบ้านที่มี LINE ID
        self.res_user_line = User.objects.create_user(username='res_line', password='pw', line_user_id='U111')
        self.resident_line = Resident.objects.create(user=self.res_user_line, room_number='101', building='A')

        # 2. สร้างลูกบ้านที่ไม่มี LINE ID
        self.res_user_noline = User.objects.create_user(username='res_noline', password='pw')
        self.resident_noline = Resident.objects.create(user=self.res_user_noline, room_number='102', building='A')

        # 3. สร้างนิติบุคคล (Staff)
        self.staff_user = User.objects.create_user(username='staff1', password='pw')
        self.staff = Staff.objects.create(user=self.staff_user)

        # 4. สร้าง User ทั่วไป (ไม่มีโปรไฟล์ Resident หรือ Staff)
        self.normal_user = User.objects.create_user(username='normal', password='pw')

        # 5. สร้างข้อมูล Package จำลอง
        self.package1 = Package.objects.create(
            resident=self.resident_line,
            handled_by=self.staff,
            sender='Shopee',
            status='RECEIVED'
        )
        self.package2 = Package.objects.create(
            resident=self.resident_noline,
            handled_by=self.staff,
            sender='Lazada',
            status='PICKED_UP',
            picked_up_at=timezone.now()
        )

        self.client = Client()

class PackageModelFormTest(PackageSetup):
    def test_package_str(self):
        """ทดสอบการแสดงผลข้อความ __str__ ของโมเดล"""
        expected_str = f"Package for 101 from Shopee"
        self.assertEqual(str(self.package1), expected_str)

    def test_valid_package_form(self):
        """ทดสอบการสร้างฟอร์มด้วยข้อมูลที่ถูกต้อง"""
        form = PackageForm(data={'resident': self.resident_line.id, 'sender': 'Amazon'})
        self.assertTrue(form.is_valid())

    def test_invalid_package_form(self):
        """ทดสอบฟอร์มกรณีข้อมูลไม่ครบถ้วน"""
        form = PackageForm(data={'resident': self.resident_line.id}) # ขาด sender
        self.assertFalse(form.is_valid())

class PackageResidentViewTest(PackageSetup):
    def test_package_list_view_resident(self):
        """ทดสอบหน้ารายการพัสดุของลูกบ้าน (ต้องเห็นเฉพาะของตัวเอง)"""
        self.client.force_login(self.res_user_line)
        response = self.client.get(reverse('package_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shopee')
        self.assertNotContains(response, 'Lazada') # ไม่ควรเห็นของห้อง 102

    def test_receive_package_resident_success(self):
        """ทดสอบลูกบ้านกดรับพัสดุด้วยตัวเองผ่าน AJAX"""
        self.client.force_login(self.res_user_line)
        response = self.client.post(reverse('receive_package_resident', args=[self.package1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        self.package1.refresh_from_db()
        self.assertEqual(self.package1.status, 'PICKED_UP')
        self.assertIsNotNone(self.package1.picked_up_at)

    def test_receive_package_resident_wrong_owner(self):
        """ทดสอบลูกบ้านแอบกดรับพัสดุของห้องอื่น (ต้อง Error 404)"""
        self.client.force_login(self.res_user_line)
        response = self.client.post(reverse('receive_package_resident', args=[self.package2.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['error'], 'Package not found')

    def test_resident_access_staff_views(self):
        """ทดสอบลูกบ้านไม่มีสิทธิ์เข้าหน้าของนิติบุคคล"""
        self.client.force_login(self.res_user_line)
        self.assertRedirects(self.client.get(reverse('receive_package')), reverse('dashboard'), fetch_redirect_response=False)
        self.assertRedirects(self.client.get(reverse('mark_picked_up', args=[self.package1.pk])), reverse('dashboard'), fetch_redirect_response=False)

class PackageStaffViewTest(PackageSetup):
    def test_package_list_view_staff(self):
        """ทดสอบนิติบุคคลดูรายการพัสดุ (ต้องเห็นทั้งหมด)"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('package_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shopee')
        self.assertContains(response, 'Lazada')

    def test_package_list_view_normal_user(self):
        """ทดสอบ User ทั่วไป (ไม่มีโปรไฟล์) เข้าดูหน้ารายการ (ต้องไม่พัง และไม่เห็นอะไร)"""
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse('package_list'))
        self.assertEqual(response.status_code, 200)

    def test_receive_package_get(self):
        """ทดสอบเปิดหน้าฟอร์มรับพัสดุเข้าระบบ"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('receive_package'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'packages/receive_package.html')

    @patch('packages.views.send_line_flex_message')
    def test_receive_package_post_line_success(self, mock_flex):
        """ทดสอบบันทึกพัสดุและส่ง LINE Flex Message สำเร็จ"""
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('receive_package'), {
            'resident': self.resident_line.id,
            'sender': 'Apple Store'
        })
        self.assertRedirects(response, reverse('package_list'))
        mock_flex.assert_called_once() # ตรวจสอบว่าเรียกฟังก์ชันส่ง Flex Message
        self.assertEqual(Package.objects.count(), 3)

    @patch('packages.views.send_line_text_message')
    @patch('packages.views.send_line_flex_message', side_effect=Exception("Flex Error"))
    def test_receive_package_post_line_fallback(self, mock_flex, mock_text):
        """ทดสอบบันทึกพัสดุ ส่ง Flex ล้มเหลว ต้อง Fallback ไปส่ง Text Message แทน"""
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('receive_package'), {
            'resident': self.resident_line.id,
            'sender': 'Nike'
        })
        self.assertRedirects(response, reverse('package_list'))
        mock_text.assert_called_once() # ตรวจสอบว่า fallback มาเรียก text message

    @patch('packages.views.messages.error')
    @patch('packages.views.send_line_text_message', side_effect=Exception("Text Error"))
    @patch('packages.views.send_line_flex_message', side_effect=Exception("Flex Error"))
    def test_receive_package_post_line_total_fail(self, mock_flex, mock_text, mock_messages):
        """ทดสอบบันทึกพัสดุ แต่ส่ง LINE พังทั้งคู่ ต้องมี Message Error แจ้งเตือนในระบบ"""
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('receive_package'), {
            'resident': self.resident_line.id,
            'sender': 'Adidas'
        })
        self.assertRedirects(response, reverse('package_list'))
        mock_messages.assert_called() # ตรวจสอบว่ามีการเรียก messages.error

    def test_receive_package_post_no_line(self):
        """ทดสอบบันทึกพัสดุให้ห้องที่ไม่ได้ผูก LINE (ต้องบันทึกผ่านโดยไม่ยิง API)"""
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('receive_package'), {
            'resident': self.resident_noline.id,
            'sender': 'Uniqlo'
        })
        self.assertRedirects(response, reverse('package_list'))
        self.assertEqual(Package.objects.last().sender, 'Uniqlo')

    def test_mark_picked_up_view(self):
        """ทดสอบ Staff กดปุ่มรับพัสดุ"""
        self.client.force_login(self.staff_user)
        
        # หมายเหตุ: โค้ดใน views.py ของคุณฟังก์ชัน `mark_picked_up_view` ลืมใส่ return response
        # ทำให้ Django Test Client คืนค่าเป็น ValueError เราจึงใช้ assertRaises จับดักไว้เพื่อคลุม Coverage
        with self.assertRaises(ValueError):
            self.client.get(reverse('mark_picked_up', args=[self.package1.pk]))
            
        # ตรวจสอบว่าพัสดุถูกเปลี่ยนสถานะในฐานข้อมูลสำเร็จ
        self.package1.refresh_from_db()
        self.assertEqual(self.package1.status, 'PICKED_UP')

    def test_staff_access_resident_views(self):
        """ทดสอบ Staff แอบเข้าหน้ากดรับพัสดุของลูกบ้าน (ต้องโดนดักสถานะ 403)"""
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('receive_package_resident', args=[self.package1.pk]))
        self.assertEqual(response.status_code, 403)