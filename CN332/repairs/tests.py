import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import RepairRequest, WorkLog, RepairImage, RepairStatusUpdate
from .forms import RepairRequestForm, UpdateRepairStatusForm
from users.models import User, Resident, Technician, Staff

class RepairSetup(TestCase):
    def setUp(self):
        # 1. สร้าง User - Resident
        self.res_user = User.objects.create_user(username='res1', password='pw')
        self.resident = Resident.objects.create(user=self.res_user, room_number='101')

        # 2. สร้าง User - Technician (แก้ไขลบ specialty ออกแล้ว)
        self.tech_user = User.objects.create_user(username='tech1', password='pw')
        self.technician = Technician.objects.create(user=self.tech_user)
        
        # ถ้าระบบ Technician มีฟิลด์ availability ให้พยายามกำหนดค่า (ถ้าไม่มี ไม่เป็นไร)
        if hasattr(self.technician, 'availability'):
            self.technician.availability = 'AVAILABLE'
            self.technician.save()

        # 3. สร้าง User - Staff
        self.staff_user = User.objects.create_user(username='staff1', password='pw')
        self.staff = Staff.objects.create(user=self.staff_user)

        # 4. สร้างตัวอย่าง RepairRequest (MAINTENANCE)
        self.repair_main = RepairRequest.objects.create(
            resident=self.resident,
            request_type='MAINTENANCE',
            location='Bathroom',
            description='Leaking pipe',
            status='PENDING'
        )

        # 5. สร้างตัวอย่าง RepairRequest (COMPLAINT)
        self.repair_comp = RepairRequest.objects.create(
            resident=self.resident,
            request_type='COMPLAINT',
            location='Lobby',
            description='Noisy neighbors',
            status='PENDING',
            assigned_staff=self.staff
        )

        self.client = Client()

class RepairModelFormTest(RepairSetup):
    def test_repair_request_str(self):
        """ทดสอบ __str__ ของ RepairRequest"""
        self.assertEqual(str(self.repair_main), "MAINTENANCE - Bathroom (PENDING)")

    def test_work_log_str(self):
        """ทดสอบ __str__ ของ WorkLog"""
        log = WorkLog.objects.create(repair_request=self.repair_main, description="Started")
        self.assertIn("Log", str(log))

    def test_repair_image_str(self):
        """ทดสอบ __str__ ของ RepairImage"""
        mock_img = SimpleUploadedFile("test.jpg", b"img", content_type="image/jpeg")
        img = RepairImage.objects.create(repair_request=self.repair_main, image=mock_img, image_type='BEFORE')
        self.assertEqual(str(img), f"BEFORE image for Request {self.repair_main.id}")

    def test_repair_request_form_valid(self):
        """ทดสอบฟอร์มสร้างแจ้งซ่อม"""
        form = RepairRequestForm(data={
            'request_type': 'MAINTENANCE',
            'location': 'Kitchen',
            'description': 'Broken sink'
        })
        self.assertTrue(form.is_valid())

class RepairResidentViewTest(RepairSetup):
    def test_repair_list_resident(self):
        """ทดสอบลูกบ้านดูรายการของตัวเอง"""
        self.client.force_login(self.res_user)
        response = self.client.get(reverse('repair_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Leaking pipe')

    def test_create_repair_with_image(self):
        """ทดสอบลูกบ้านสร้างรายการแจ้งซ่อมพร้อมแนบรูป"""
        self.client.force_login(self.res_user)
        
        images_data = json.dumps([{'id': '1', 'type': 'BEFORE'}])
        mock_img = SimpleUploadedFile("test.jpg", b"img_data", content_type="image/jpeg")
        
        response = self.client.post(reverse('create_repair'), {
            'request_type': 'MAINTENANCE',
            'location': 'Bedroom',
            'description': 'AC not working',
            'images_data': images_data,
            'image_1': mock_img
        })
        self.assertRedirects(response, reverse('repair_list'), fetch_redirect_response=False)
        self.assertEqual(RepairRequest.objects.count(), 3)
        self.assertEqual(RepairImage.objects.count(), 1) # เช็กว่ารูปถูกอัปโหลดสำเร็จ

    def test_rate_repair_success(self):
        """ทดสอบลูกบ้านให้คะแนนงานที่เสร็จแล้ว"""
        self.client.force_login(self.res_user)
        # จำลองสถานะเป็น COMPLETED ก่อนถึงจะให้คะแนนได้
        self.repair_main.status = 'COMPLETED'
        self.repair_main.save()

        response = self.client.post(reverse('rate_repair', args=[self.repair_main.pk]), {'rating': '5'})
        self.assertRedirects(response, reverse('repair_list'), fetch_redirect_response=False)
        self.repair_main.refresh_from_db()
        self.assertEqual(self.repair_main.rating, 5)

class RepairStaffViewTest(RepairSetup):
    def test_repair_list_staff(self):
        """ทดสอบนิติบุคคลเข้าดูรายการรวมทั้งหมด"""
        self.client.force_login(self.staff_user)
        response = self.client.get(reverse('repair_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Leaking pipe')
        self.assertContains(response, 'Noisy neighbors')

    def test_assign_technician(self):
        """ทดสอบนิติบุคคลจ่ายงานให้ช่าง (MAINTENANCE)"""
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('assign_technician', args=[self.repair_main.pk]), {
            'technician': self.technician.pk
        })
        self.assertRedirects(response, reverse('repair_list'), fetch_redirect_response=False)
        self.repair_main.refresh_from_db()
        self.assertEqual(self.repair_main.technician, self.technician)

    def test_update_complaint_status_by_staff(self):
        """ทดสอบนิติบุคคลอัปเดตสถานะเรื่องร้องเรียนในหน้า detail"""
        self.client.force_login(self.staff_user)
        response = self.client.post(reverse('repair_detail', args=[self.repair_comp.pk]), {
            'status': 'ON_PROCESS',
            'work_note': 'Contacted the neighbor.'
        })
        self.assertRedirects(response, reverse('repair_detail', args=[self.repair_comp.pk]), fetch_redirect_response=False)
        self.repair_comp.refresh_from_db()
        self.assertEqual(self.repair_comp.status, 'ON_PROCESS')
        self.assertTrue(WorkLog.objects.filter(repair_request=self.repair_comp, description='Contacted the neighbor.').exists())

class RepairTechnicianViewTest(RepairSetup):
    def setUp(self):
        super().setUp()
        # มอบหมายงานให้ช่างก่อนเริ่มเทสต์
        self.repair_main.technician = self.technician
        self.repair_main.save()

    def test_update_repair_status_by_tech(self):
        """ทดสอบช่างอัปเดตสถานะงานซ่อมเป็นเสร็จสิ้น พร้อมแนบรูป AFTER"""
        self.client.force_login(self.tech_user)
        
        # สร้าง Byte โค้ดของรูปภาพ GIF ขนาด 1x1 พิกเซลของจริง เพื่อให้ผ่าน Validation ของ ImageField
        valid_image_bytes = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
            b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        )
        mock_img = SimpleUploadedFile("after.gif", valid_image_bytes, content_type="image/gif")
        
        response = self.client.post(reverse('update_repair_status', args=[self.repair_main.pk]), {
            'status': 'COMPLETED',
            'note': 'Fixed the pipe.',
            'image': mock_img
        })
        self.assertRedirects(response, reverse('repair_detail', args=[self.repair_main.pk]), fetch_redirect_response=False)
        
        self.repair_main.refresh_from_db()
        self.assertEqual(self.repair_main.status, 'COMPLETED')
        self.assertTrue(RepairStatusUpdate.objects.filter(repair_request=self.repair_main, status='COMPLETED').exists())
        self.assertTrue(RepairImage.objects.filter(repair_request=self.repair_main, image_type='AFTER').exists())

    def test_technician_work_history(self):
        """ทดสอบหน้าประวัติการทำงานของช่าง พร้อมการใช้ Filter"""
        self.client.force_login(self.tech_user)
        
        # จำลองงานที่เสร็จแล้ว
        self.repair_main.status = 'COMPLETED'
        self.repair_main.rating = 4
        self.repair_main.save()

        # ทดสอบเข้าหน้า history พร้อมส่ง Filter ไปด้วย
        response = self.client.get(reverse('technician_work_history'), {
            'q': 'Bathroom',
            'date_range': '30',
            'repair_type': 'MAINTENANCE',
            'rating': '4'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bathroom')
        self.assertEqual(response.context['avg_rating'], 4.0)
        self.assertEqual(response.context['total_completed'], 1)