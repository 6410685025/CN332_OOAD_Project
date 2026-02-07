# CN332 Project – Context & Handoff for New Chat

เอกสารนี้สรุปบริบทโปรเจกต์ สิ่งที่คุยและทำไปแล้วใน chat ก่อนหน้า และแผนในอนาคต เพื่อให้ chat ตัวใหม่ทำงานต่อได้สะดวก

---

## 1. โปรเจกต์คืออะไร

- **ชื่อ:** โปรเจกต์ CN332 – ระบบบริหารจัดการหอ/คอนโด (Condo / Apartment Management)
- **Tech:** Django (Python), HTML templates, Bootstrap 5, Bootstrap Icons, CSS ใน `static/css/theme.css`
- **Domain model:** อ้างอิงจาก `latest_classDiagram.txt` (User/Resident/Staff/Technician, RepairRequest/WorkLog, Facility/Booking, Package, Announcement, LostFound + enums)

---

## 2. สิ่งที่คุยและทำไปแล้วใน chat นี้

### 2.1 การออกแบบจาก Figma
- มีโฟลเดอร์ `figma_example/CN332/` เป็นภาพอ้างอิงจาก Figma (Dashboard, Bookings, Repair, Package, Announcement, Lost & Found, Settings, Residents, Notifications ฯลฯ)
- ตกลงลำดับการทำ: ฐานร่วม → Dashboard → Facility → Repair → Package → Announcement → Lost & Found → Residents + Settings

### 2.2 สิ่งที่ implement แล้ว
- **Base:** `templates/base.html` + `static/css/theme.css` – sidebar น้ำเงินเข้ม (Figma), เมนูเรียงตาม Figma, เน้นเมนูตาม `url_name`
- **Dashboards:** Resident / Staff / Technician ตาม layout และการ์ดแบบ Figma
- **Facility:** หน้า Facility Booking (การ์ด facility), Check Availability ลิงก์ไปฟอร์มจองพร้อม `?facility=id`, My Bookings (resident), หน้าจอง + รายการจอง
- **Repair/Request:** รายการคำร้อง + ช่องค้นหา + ตาราง + New Request, หน้ารายละเอียดคำร้อง, Assign Technician, Update Status, Rate
- **Package:** Package Tracking (resident + staff), Receive Package, Mark Picked Up
- **Announcement:** รายการประกาศ (Community Announcements), ฟอร์มสร้างประกาศ (staff)
- **Lost & Found:** รายการ + แจ้งของ + Resolve (staff)
- **Residents [Staff]:** หน้ารายชื่อ residents (`/residents/`)
- **Settings:** หน้า Settings พื้นฐาน (`/settings/`) – โปรไฟล์, Residence info (resident), Change Password / Save ยังไม่ทำงาน
- **User model:** `is_resident`, `is_staff_member`, `is_technician` เป็น `@property` เพื่อใช้ในเทมเพลต
- **Login:** ใช้ `/login/` – user ปกติต้องมีโปรไฟล์ Resident/Staff/Technician ใน Admin ถึงจะเข้า Dashboard ได้ (ไม่มีแค่ admin อย่างเดียว)

### 2.3 ปัญหาที่แก้ไปแล้ว
- พอร์ต 8000 ถูกใช้: แนะนำให้รัน `runserver 8080` หรือ kill process ที่ใช้พอร์ต 8000
- User ปกติเข้าได้: อธิบายว่าต้องสร้าง User ใน Admin แล้วเพิ่ม Resident/Staff/Technician profile

---

## 3. สิ่งที่ยังไม่ทำ / ยังไม่สมบูรณ์ (เทียบกับ Figma)

- **Check Availability:** หน้า "Select Date & Time" แบบปฏิทิน + ปุ่ม time slots (และแสดง slot ที่ไม่ว่าง) – ตอนนี้มีแค่ฟอร์มจองธรรมดา
- **Notifications:** ยังไม่มีระบบแจ้งเตือน (dropdown หรือหน้าแจ้งเตือน การ์ดแบบ "New Package Arrived!", "Booking Confirmed" ตาม noti 1, noti 2)
- **Announcement:** ยังไม่มี category (NEW, Emergency, General, …), ยังไม่มีหน้ารายละเอียดประกาศ และลิงก์ "Read more" ยังไม่ไปหน้าที่มีอยู่
- **Settings:** แท็บ Security, ฟอร์ม Change Password, ปุ่ม Save ที่บันทึกโปรไฟล์จริง ยังไม่ implement
- **Facility cards:** ยังใช้ gradient/placeholder แทนรูป facility จริง
- **All Bookings (Staff):** ปรับ badge/layout ให้ตรง Figma
- **Repair Detail:** ปรับ layout/การ์ด/Work log ให้ตรง Figma

---

## 4. แผนในอนาคตของโปรเจกต์ (ที่คุยไว้)

### 4.1 Logic / Business
- จอง Facility ไม่ให้ชนเวลา: เพิ่ม `Facility.check_availability(date, time_slot)` และใช้ในฟอร์ม/ view
- Booking หมดอายุอัตโนมัติ: ใช้สถานะ EXPIRED กับ management command หรือ cron
- Technician รับงานเอง (accept repair)
- Resident ยืนยันการจอง (confirm booking) ถ้าต้องการ
- ย้าย business logic เข้า model methods (Booking.confirm/cancel, Package.mark_received/mark_picked_up, RepairRequest.close_request ฯลฯ)

### 4.2 UX / หน้าเว็บ
- Search/Filter จริงใน Announcements, Lost & Found, Repair list
- หน้า Announcement detail + "Read more"
- Settings ให้แก้ไขได้ + Change Password
- Responsive (มือถือ/แท็บเล็ต)

### 4.3 ฟีเจอร์เสริม
- แจ้งเตือนแบบง่าย (badge ตัวเลขบนเมนู)
- อัปโหลดรูป Lost & Found
- Export รายงาน (CSV/Excel) สำหรับ staff
- Unit tests

### 4.4 สมบูรณ์ตาม Figma
- หน้า Check Availability แบบ calendar + time slots
- ระบบ Notifications (การ์ด Package/Booking)
- Announcement category + detail
- Settings ครบ (Security, Change Password, Save)
- รูป Facility จริง (เมื่อมีไฟล์)
- ปรับ All Bookings และ Repair Detail ให้ตรง Figma

---

## 5. โครงสร้างที่สำคัญ

- **รากโปรเจกต์:** `condo_project/`, `users/`, `repairs/`, `facilities/`, `packages/`, `announcements/`, `lost_found/`
- **Template หลัก:** `templates/base.html` (sidebar + content-inner)
- **CSS ธีม:** `static/css/theme.css` (ตัวแปรสี, sidebar, card, badge-pill ฯลฯ)
- **Domain อ้างอิง:** `latest_classDiagram.txt`
- **อ้างอิงดีไซน์:** `figma_example/CN332/*.png`

---

## 6. หมายเหตุสำหรับ chat ตัวใหม่

- ล็อกอิน user ปกติ: สร้าง User ใน Django Admin แล้วเพิ่ม **Resident** หรือ **Staff** หรือ **Technician** (อย่างใดอย่างหนึ่ง) ให้กับ User นั้น
- ใช้ `request.user.is_resident` / `is_staff_member` / `is_technician` (property ไม่มีวงเล็บ)
- URL names หลัก: `dashboard`, `resident_dashboard`, `staff_dashboard`, `technician_dashboard`, `facility_list`, `create_booking`, `my_bookings`, `repair_list`, `create_repair`, `repair_detail`, `package_list`, `announcement_list`, `lost_found_list`, `residents_list`, `settings`
