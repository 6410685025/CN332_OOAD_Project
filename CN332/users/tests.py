import json
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages.storage.fallback import FallbackStorage

from .models import Resident, Staff, Technician
from repairs.models import RepairRequest
from .forms import ResidentCreationForm
from .services.line_messaging import _push_line_message, send_line_text_message, send_line_flex_message
from .adapters import NoNewSocialSignupAdapter
from allauth.exceptions import ImmediateHttpResponse
from .views import social_connections_view

User = get_user_model()

class UserSetup(TestCase):
    def setUp(self):
        # 1. สร้าง User ที่เป็น Resident
        self.res_user = User.objects.create_user(
            username='resident1', password='password123', 
            first_name='John', last_name='Doe', email='john@test.com'
        )
        self.resident = Resident.objects.create(
            user=self.res_user, room_number='101', building='A', floor='1'
        )

        # 2. สร้าง User ที่เป็น Staff
        self.staff_user = User.objects.create_user(
            username='staff1', password='password123',
            first_name='Jane', last_name='Smith'
        )
        self.staff = Staff.objects.create(user=self.staff_user, position='Manager')

        # 3. สร้าง User ที่เป็น Technician
        self.tech_user = User.objects.create_user(
            username='tech1', password='password123',
            first_name='Bob', last_name='Fixer'
        )
        self.technician = Technician.objects.create(user=self.tech_user, availability='AVAILABLE')

        # 4. สร้าง User ธรรมดา (ไม่มี Role)
        self.normal_user = User.objects.create_user(username='normal', password='pw')

        self.client = Client()

class UserModelAndFormTest(UserSetup):
    def test_user_properties(self):
        self.assertTrue(self.res_user.is_resident)
        self.assertFalse(self.res_user.is_staff_member)
        self.assertTrue(self.staff_user.is_staff_member)
        self.assertTrue(self.tech_user.is_technician)

    def test_model_str(self):
        self.assertEqual(str(self.resident), "resident1 - 101")
        self.assertEqual(str(self.staff), "staff1 - Manager")
        self.assertEqual(str(self.technician), "tech1 (AVAILABLE)")

    def test_resident_creation_form_invalid(self):
        # รหัสผ่านไม่ตรงกัน
        form1 = ResidentCreationForm(data={
            'username': 'newuser', 'email': 'new@test.com',
            'first_name': 'New', 'last_name': 'User',
            'password': 'password123', 'password_confirm': 'password456', 
            'building': 'B', 'floor': 2, 'room_number': '202'
        })
        self.assertFalse(form1.is_valid())
        
        # Username/Email ซ้ำ
        form2 = ResidentCreationForm(data={
            'username': 'resident1', 'email': 'john@test.com',
            'first_name': 'New', 'last_name': 'User',
            'password': 'password123', 'password_confirm': 'password123', 
            'building': 'B', 'floor': 2, 'room_number': '202'
        })
        self.assertFalse(form2.is_valid())

class AuthAndDashboardTest(UserSetup):
    def test_login_logout_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.res_user)
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'), fetch_redirect_response=False)

    def test_dashboard_redirects_and_error(self):
        self.client.force_login(self.res_user)
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('resident_dashboard'), fetch_redirect_response=False)
        
        self.client.force_login(self.staff_user)
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('staff_dashboard'), fetch_redirect_response=False)
        
        self.client.force_login(self.tech_user)
        self.assertRedirects(self.client.get(reverse('dashboard')), reverse('technician_dashboard'), fetch_redirect_response=False)
        
        # ทดสอบ User ธรรมดา (ไม่มี Role) เข้าหน้า Dashboard ต้องเจอหน้า Error
        self.client.force_login(self.normal_user)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard_error.html')

    def test_dashboards_rendering(self):
        """ทดสอบโหลดหน้า Dashboard แต่ละ Role เพื่อเก็บ Coverage การเตรียม Context"""
        self.client.force_login(self.res_user)
        self.assertEqual(self.client.get(reverse('resident_dashboard')).status_code, 200)

        self.client.force_login(self.staff_user)
        self.assertEqual(self.client.get(reverse('staff_dashboard')).status_code, 200)
        self.assertEqual(self.client.get(reverse('residents_list')).status_code, 200)

        self.client.force_login(self.tech_user)
        self.assertEqual(self.client.get(reverse('technician_dashboard')).status_code, 200)

    def test_staff_dashboard_filters_repairs_by_status(self):
        RepairRequest.objects.create(
            resident=self.resident,
            request_type='MAINTENANCE',
            description='Pending repair',
            location='A1',
            status='PENDING'
        )
        RepairRequest.objects.create(
            resident=self.resident,
            request_type='MAINTENANCE',
            description='In progress repair',
            location='A2',
            status='ON_PROCESS'
        )
        RepairRequest.objects.create(
            resident=self.resident,
            request_type='MAINTENANCE',
            description='Completed repair',
            location='A3',
            status='COMPLETED'
        )

        self.client.force_login(self.staff_user)

        completed_response = self.client.get(reverse('staff_dashboard'), {'status': 'COMPLETED'})
        self.assertEqual(completed_response.status_code, 200)
        self.assertEqual(completed_response.context['selected_repair_status'], 'COMPLETED')
        self.assertEqual(completed_response.context['filtered_repairs_total'], 1)
        self.assertTrue(all(r.status == 'COMPLETED' for r in completed_response.context['recent_repairs']))

        invalid_response = self.client.get(reverse('staff_dashboard'), {'status': 'INVALID'})
        self.assertEqual(invalid_response.status_code, 200)
        self.assertEqual(invalid_response.context['selected_repair_status'], 'ALL')
        self.assertEqual(invalid_response.context['filtered_repairs_total'], 3)

class ResidentCRUDTest(UserSetup):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.staff_user)

    def test_create_resident_ajax_success(self):
        data = {
            'username': 'newres', 'email': 'newres@test.com',
            'first_name': 'Tom', 'last_name': 'Cat',
            'password': 'password123', 'password_confirm': 'password123',
            'building': 'C', 'floor': '3', 'room_number': '301'
        }
        response = self.client.post(reverse('create_resident'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

    def test_create_resident_ajax_invalid_form(self):
        response = self.client.post(reverse('create_resident'), {})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    @patch('users.views.User.objects.create_user', side_effect=Exception('DB Error Mock'))
    def test_create_resident_ajax_exception(self, mock_create):
        """ทดสอบจำลอง DB Error ตอนสร้างลูกบ้าน"""
        data = {
            'username': 'newres', 'email': 'newres@test.com',
            'first_name': 'Tom', 'last_name': 'Cat',
            'password': 'password123', 'password_confirm': 'password123',
            'building': 'C', 'floor': '3', 'room_number': '301'
        }
        response = self.client.post(reverse('create_resident'), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('DB Error Mock', response.json()['error'])

    def test_get_resident_ajax(self):
        response = self.client.get(reverse('get_resident', args=[self.resident.id]))
        self.assertEqual(response.status_code, 200)
        
        # Test Not Found
        response = self.client.get(reverse('get_resident', args=[999]))
        self.assertEqual(response.status_code, 404)

    def test_update_resident_ajax(self):
        data = {'first_name': 'Johnny'}
        response = self.client.put(reverse('update_resident', args=[self.resident.id]), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Test Not Found
        response = self.client.put(reverse('update_resident', args=[999]), '{}', content_type='application/json')
        self.assertEqual(response.status_code, 404)

    @patch('users.models.Resident.save', side_effect=Exception('Save Error'))
    def test_update_resident_ajax_exception(self, mock_save):
        data = {'first_name': 'Johnny'}
        response = self.client.put(reverse('update_resident', args=[self.resident.id]), json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Save Error', response.json()['error'])

    def test_delete_resident_ajax(self):
        response = self.client.delete(reverse('delete_resident', args=[self.resident.id]))
        self.assertEqual(response.status_code, 200)
        
        # Test Not Found
        response = self.client.delete(reverse('delete_resident', args=[999]))
        self.assertEqual(response.status_code, 404)

    @patch('users.models.Resident.delete', side_effect=Exception('Delete Error'))
    def test_delete_resident_ajax_exception(self, mock_delete):
        response = self.client.delete(reverse('delete_resident', args=[self.resident.id]))
        self.assertEqual(response.status_code, 400)
        self.assertIn('Delete Error', response.json()['error'])

class SettingsAndLINEIntegrationTest(UserSetup):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.res_user)

    def test_update_profile(self):
        """ทดสอบการอัปเดตโปรไฟล์ส่วนตัว"""
        # สร้าง Byte โค้ดของรูปภาพ GIF ขนาด 1x1 พิกเซลของจริง เพื่อให้ผ่าน Validation ของ ImageField
        valid_image_bytes = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff'
            b'\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00'
            b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
        )
        valid_image = SimpleUploadedFile("avatar.gif", valid_image_bytes, content_type="image/gif")
        
        data = {
            'first_name': 'Jane', 'last_name': 'Doe', 
            'email': 'jane@test.com', 'contact_number': '0999999999',
            'profile_photo': valid_image
        }
        
        response = self.client.post(reverse('update_profile'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        
        self.res_user.refresh_from_db()
        self.assertEqual(self.res_user.first_name, 'Jane')

    def test_update_profile_invalid(self):
        response = self.client.post(reverse('update_profile'), {})
        self.assertEqual(response.status_code, 400)

    @patch('users.forms.ResidentProfileForm.save', side_effect=Exception('Form Save Error'))
    def test_update_profile_exception(self, mock_save):
        data = {'first_name': 'Jane', 'last_name': 'Doe', 'email': 'jane@test.com'}
        response = self.client.post(reverse('update_profile'), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Form Save Error', response.json()['error'])

    def test_change_password(self):
        data = {'old_password': 'password123', 'new_password1': 'NewPass123!', 'new_password2': 'NewPass123!'}
        response = self.client.post(reverse('change_password'), data)
        self.assertEqual(response.status_code, 200)

    def test_change_password_invalid(self):
        response = self.client.post(reverse('change_password'), {})
        self.assertEqual(response.status_code, 400)

    @patch('users.forms.ResidentPasswordChangeForm.save', side_effect=Exception('PW Error'))
    def test_change_password_exception(self, mock_save):
        data = {'old_password': 'password123', 'new_password1': 'NewPass123!', 'new_password2': 'NewPass123!'}
        response = self.client.post(reverse('change_password'), data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('PW Error', response.json()['error'])

    @patch('users.views.settings.LINE_CHANNEL_ID', None)
    def test_line_connect_no_settings(self):
        """ทดสอบกดลิงก์ LINE แต่ระบบไม่ได้ตั้งค่า Token ไว้"""
        response = self.client.get(reverse('line_connect'))
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)

    @patch('users.views.settings.LINE_CHANNEL_ID', 'test_id')
    @patch('users.views.settings.LINE_CHANNEL_SECRET', 'test_secret')
    def test_line_connect_success(self):
        response = self.client.get(reverse('line_connect'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('access.line.me', response.url)

    def test_line_callback_errors(self):
        """ทดสอบเคส Error ต่างๆ ของการ Callback จาก LINE"""
        # 1. Error จาก GET param
        response = self.client.get(reverse('line_callback'), {'error': 'access_denied'})
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)
        
        # 2. State ไม่ตรงกัน
        session = self.client.session
        session['line_oauth_state'] = 'correct_state'
        session.save()
        response = self.client.get(reverse('line_callback'), {'state': 'wrong_state'})
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)

        # 3. ไม่มี Code
        response = self.client.get(reverse('line_callback'), {'state': 'correct_state'})
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)

    @patch('users.views.requests.post')
    def test_line_callback_token_failed(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400 # Token API พัง
        mock_post.return_value = mock_response
        
        session = self.client.session
        session['line_oauth_state'] = 'state123'
        session.save()

        response = self.client.get(reverse('line_callback'), {'state': 'state123', 'code': 'abc'})
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)

    @patch('users.views.requests.post')
    @patch('users.views.requests.get')
    def test_line_callback_profile_failed(self, mock_get, mock_post):
        # Mock Token Success
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {'access_token': 'fake_token'}
        mock_post.return_value = mock_post_resp
        
        # Mock Profile Failed
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 400 
        mock_get.return_value = mock_get_resp

        session = self.client.session
        session['line_oauth_state'] = 'state123'
        session.save()

        response = self.client.get(reverse('line_callback'), {'state': 'state123', 'code': 'abc'})
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)

    @patch('users.views.requests.post')
    @patch('users.views.requests.get')
    def test_line_callback_existing_user(self, mock_get, mock_post):
        # สร้าง User อื่นที่ผูก LINE ID นี้ไว้แล้ว
        User.objects.create_user(username='other', line_user_id='U999')

        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {'access_token': 'fake_token'}
        mock_post.return_value = mock_post_resp
        
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200 
        mock_get_resp.json.return_value = {'userId': 'U999'}
        mock_get.return_value = mock_get_resp

        session = self.client.session
        session['line_oauth_state'] = 'state123'
        session.save()

        response = self.client.get(reverse('line_callback'), {'state': 'state123', 'code': 'abc'})
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)
        self.assertNotEqual(self.res_user.line_user_id, 'U999') # ต้องผูกไม่สำเร็จ

    def test_line_disconnect(self):
        self.res_user.line_user_id = 'U123'
        self.res_user.save()
        response = self.client.post(reverse('line_disconnect'))
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)
        self.res_user.refresh_from_db()
        self.assertIsNone(self.res_user.line_user_id)

    def test_social_disconnect_empty(self):
        """ทดสอบการถอด Social Account (Allauth) แต่ไม่ส่ง ID มา"""
        response = self.client.post(reverse('social_disconnect'))
        self.assertRedirects(response, reverse('settings'), fetch_redirect_response=False)

    @patch('users.views.connections')
    def test_social_connections_view(self, mock_connections):
        """ทดสอบ View ที่เอาไว้จัดการเชื่อมต่อ Social (Google/Facebook)"""
        factory = RequestFactory()
        request = factory.post('/fake-url/')
        request.user = self.res_user
        
        response = social_connections_view(request)
        self.assertEqual(response.status_code, 302)
        mock_connections.assert_called_once()
        
        request_get = factory.get('/fake-url/')
        request_get.user = self.res_user
        response_get = social_connections_view(request_get)
        self.assertEqual(response_get.status_code, 302)

class LineMessagingServiceTest(TestCase):
    @patch('users.services.line_messaging.settings')
    def test_no_token(self, mock_settings):
        """ทดสอบกรณีลืมใส่ Token ของ LINE ใน Settings"""
        mock_settings.LINE_OA_CHANNEL_ACCESS_TOKEN = None
        with self.assertRaises(RuntimeError):
            _push_line_message({})

    @patch('users.services.line_messaging.requests.post')
    def test_push_line_message_success(self, mock_post):
        """ทดสอบยิง API ไปหา LINE สำเร็จ"""
        mock_response = MagicMock()
        mock_response.content = b'{"message": "success"}'
        mock_response.json.return_value = {"message": "success"}
        mock_post.return_value = mock_response

        res = send_line_text_message('U123', 'Hello Test')
        self.assertEqual(res['message'], 'success')

        res2 = send_line_flex_message('U123', 'Alt Text', {'type': 'bubble'})
        self.assertEqual(res2['message'], 'success')

class AllauthAdapterTest(TestCase):
    def test_no_new_social_signup_adapter(self):
        """ทดสอบ Adapter ป้องกันการสมัครผ่าน Social ถ้าไม่มีบัญชีอยู่ก่อนแล้ว"""
        adapter = NoNewSocialSignupAdapter()
        request = MagicMock()
        request.user.is_authenticated = False
        
        sociallogin = MagicMock()
        sociallogin.is_existing = False
        
        # 1. ต้องขัดขวางและโยน Error (ImmediateHttpResponse)
        with self.assertRaises(ImmediateHttpResponse):
            adapter.pre_social_login(request, sociallogin)
            
        # 2. ปิดไม่ให้ Signup
        self.assertFalse(adapter.is_open_for_signup(request, sociallogin))
        
        # 3. ตรวจสอบ Redirect URLs
        self.assertEqual(adapter.get_connect_redirect_url(request, sociallogin), '/settings/')
        self.assertEqual(adapter.get_disconnect_redirect_url(request, sociallogin), '/settings/')