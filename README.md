# CN332 OOAD Project 


### 📄 Project Documentation

📘 **System Design Document**  
👉 [Design Document](https://github.com/6410685025/CN332_OOAD_Project/blob/main/Design_Homie.pdf)

📘 **Account Access by Role Document**  
👉 [Account Access by Role](https://github.com/6410685025/CN332_OOAD_Project/blob/main/AccountAccessByRole_Homie.pdf)

🎥 **Project Demo Video**  
👉 [Watch Demo](https://youtu.be/9Y_eJGH7YfE)

---

### 📌 Iteration Timeline

- **Iteration 1 – concept**  
  👉 [View Presentation](https://www.canva.com/design/DAG-HY_74Ag/q1fy_Gew59aYLj1mKFYubQ/view?utm_content=DAG-HY_74Ag&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=hfee62794df)

- **Iteration 2 – การแจกแจง requirement**  
  👉 [View Presentation](https://www.canva.com/design/DAG_aEF_Qgc/ytWRaUr3ibhL8VGq54ei7g/view?utm_content=DAG_aEF_Qgc&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=hdb861da272)

- **Iteration 3 –  use case diagram และ class diagram**  
  👉 [View Presentation](https://www.canva.com/design/DAG_aDzLJkA/266cjUHBc4y0rqxT8fF_Gw/view?utm_content=DAG_aDzLJkA&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=hc62ddb5a70)
  
- **Iteration 4 –  GUI & CLI**  
  👉 [View Presentation](https://www.canva.com/design/DAHAEKZlnGw/ZYkHSRz5ktaqcwCcBPNoRg/view?utm_content=DAHAEKZlnGw&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h8b89ea9c49)
  👉 [link Figma](https://www.figma.com/proto/ozO6fIHf4kVpGhM5CMUrXz/CN332?node-id=0-1&t=bxEUX6ScdwMKQKGM-1)

- **Iteration 5 –  requirent-> implementation**  
  👉 [View Presentation](https://www.canva.com/design/DAHAnygwA58/4ijC4TgvWzVLvlnkJDayLw/view?utm_content=DAHAnygwA58&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h024b39c394)

- **Iteration 6 –  Implement user / login**

   👉 [View Presentation](https://www.canva.com/design/DAHBSm8C3ak/AmCgWYoRtgMes533DgR9CQ/view?utm_content=DAHBSm8C3ak&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h17e7430860)
   📌 **Presented in Class — 16 February 2026**

- **Iteration 7 –  Implement plan**

  👉 [View Presentation](https://www.canva.com/design/DAHDPyPor9A/rXBbGE3GPczLKtlRI2oZNQ/view?utm_content=DAHDPyPor9A&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h21a50d5239)
  📌 **Presented in Class — 27 April 2026**

- **Final Present**

  👉 [View Presentation](https://canva.link/w55bfnkfulp7tdb)
  📌 **Presented in Class — 18 May 2026**

  

 

---
## 🏘 Overview
Web Application สำหรับ **บ้านจัดสรร คอนโด และหอพัก**  
ที่ช่วยอำนวยความสะดวกให้ลูกบ้านและนิติบุคคล  
โดยใช้ **LINE Official Account (LINE OA)** เป็นช่องทางแจ้งเตือนหลัก

ระบบถูกออกแบบตามแนวคิด  
**Object-Oriented Analysis and Design (OOAD)**  
เพื่อให้โครงสร้างชัดเจน ยืดหยุ่น และรองรับการขยายในอนาคต

---

## 🎯 Project Objectives
- รวมบริการสำคัญของโครงการไว้ในระบบเดียว
- ลดภาระการติดต่อแบบออฟไลน์
- ลดการพลาดข้อมูลสำคัญของลูกบ้าน
- ใช้ LINE เป็นช่องทางแจ้งเตือนหลัก
- ออกแบบระบบให้สอดคล้องกับ OOAD

---

## 👥 User Roles

### 👤 Resident (ลูกบ้าน)
- ใช้งานผ่าน Web Application / LINE
- รับแจ้งเตือนผ่าน LINE ส่วนตัว
- เป็นผู้เริ่มต้นการใช้งานฟีเจอร์หลักของระบบ

### 🏢 Admin / Staff (นิติบุคคล)
- จัดการข้อมูลและกระบวนการทำงาน
- ควบคุมและกลั่นกรองข้อมูล
- ดูแลการสื่อสารกับลูกบ้าน

### 🛠 Technician (ช่าง)
- รับและดำเนินการงานซ่อม
- อัปเดตสถานะการทำงาน

---

## 🧩 System Features

### 🔧 1. Maintenance & Complaint System
ระบบแจ้งซ่อมและร้องเรียนภายในโครงการ

**Resident**
- แจ้งปัญหาซ่อม/ร้องเรียน
- ติดตามสถานะงาน
- ให้คะแนนความพึงพอใจหลังงานเสร็จ

**Admin / Staff**
- ตรวจสอบและมอบหมายงาน
- ติดตามความคืบหน้า

**Technician**
- รับงานซ่อม
- อัปเดตสถานะ
- ดำเนินการแก้ไขปัญหา

> ระบบแจ้งเตือนสถานะงานผ่าน LINE OA

---

### 🏟 2. Facility Reservation System
ระบบจองพื้นที่ส่วนกลาง เช่น สระว่ายน้ำ ฟิตเนส ห้องประชุม

**Resident**
- ตรวจสอบความว่าง
- จอง / ยกเลิกการจอง
- ยืนยันการจองก่อนถึงเวลาใช้งาน
- รับแจ้งเตือนผ่าน LINE

**Admin**
- จัดการข้อมูลพื้นที่ส่วนกลาง
- ตรวจสอบประวัติการจอง

---

### 📦 3. Parcel Notification System
ระบบแจ้งเตือนพัสดุ (เหมาะสำหรับคอนโดและหอพัก)

**Resident**
- ดูรายการพัสดุ
- ตรวจสอบสถานะ
- รับแจ้งเตือนเมื่อพัสดุมาถึง

**Admin / Staff**
- บันทึกข้อมูลพัสดุ
- อัปเดตสถานะพัสดุ

---

### 🔍 4. Lost & Found Management
ระบบแจ้งของหายและหาเจ้าของ (มีการกลั่นกรอง)

**Resident**
- แจ้งของหาย / พบของตกหล่น
- ดูรายการที่ได้รับอนุมัติแล้ว

**Admin**
- ตรวจสอบและอนุมัติข้อมูล

---

### 📢 5. Announcement & Notification System
ระบบประกาศข่าวสารและแจ้งเตือนสำคัญ

**Admin**
- สร้างและเผยแพร่ประกาศ
- เลือกกลุ่มเป้าหมาย
- ส่งแจ้งเตือนผ่าน LINE OA

**Resident**
- รับแจ้งเตือน
- ดูประกาศย้อนหลัง

---

### 🔗 6. LINE OA Integration
ใช้ LINE Official Account เป็น Notification Channel หลัก

- Account Linking ระหว่างผู้ใช้กับ LINE
- แจ้งเตือนอัตโนมัติ:
  - งานแจ้งซ่อม
  - การจองพื้นที่ส่วนกลาง
  - เตือนก่อนถึงเวลาจอง
  - พัสดุมาถึง
  - ประกาศข่าวสาร
- ผู้ใช้สามารถยกเลิกการเชื่อมต่อ LINE ได้

---

## 📌 Example Use Cases

### Maintenance Request
1. Resident แจ้งปัญหาผ่านเว็บ
2. Admin มอบหมายงาน
3. Technician ดำเนินการซ่อม
4. Resident ให้คะแนน
5. ระบบแจ้งเตือนผ่าน LINE

### Facility Reservation
1. Resident จองพื้นที่
2. Resident ยืนยันการจอง
3. ระบบแจ้งเตือนและเตือนล่วงหน้า

---


## Members  
| No. | Name | Student ID | 
|-----|------|-------------|
| 1 | **รัชพล	 เยี่ยมกระโทก** | 6410455015 | 
| 2 | **กนกวรรณ คุ้มโชคชนะ** | 6410615014 | 
| 3 | **อรรคพล เมืองฮาม** | 6410685025 |
| 4 | **ธวัลภรณ์ จินดาวรานน์** | 6610545029 |
