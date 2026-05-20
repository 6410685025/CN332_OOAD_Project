# Interactive CLI System for Condo Management

Interactive command-line interface dashboard สำหรับบริหารจัดการระบบ Condo "Homie" สำหรับแต่ละ role

---

## 📋 Overview

ระบบ CLI มี 4 interactive dashboard สำหรับแต่ละ user role:

| Role | Command | Purpose |
|------|---------|---------|
| 👥 **Resident** | `python manage.py resident_cli aomnaiiii` | Manage own bookings, packages, repairs, lost/found items |
| 👔 **Staff** | `python manage.py staff_cli staff1` | Create announcements, register packages, manage bookings |
| 🔧 **Technician** | `python manage.py technician_cli tech1` | View assigned repairs, update status, add logs |
| 👨‍⚖️ **Juristic** | `python manage.py juristic_cli staff1` | View pending requests, confirm and assign to technicians |

---

## 🏠 RESIDENT CLI

### Usage
```bash
python manage.py resident_cli aomnaiiii
```

### Dashboard Menu
```
╔═══════════════════════════════════════════════════════════════╗
║                    RESIDENT DASHBOARD                         ║
╚═══════════════════════════════════════════════════════════════╝

[1] View Bookings
[2] Manage Bookings
[3] View Packages
[4] Manage Repairs
[5] Lost & Found
[0] Logout
```

### Features

#### 📅 Booking Management
- **View Bookings**: Display all bookings with status (PENDING/CONFIRMED/CANCELLED/EXPIRED)
- **Create Booking**: Select facility → enter date & time → confirm
- **Cancel Booking**: Enter booking ID and confirm cancellation

#### 📦 Packages
- **View Packages**: See all packages with arrival time and status

#### 🔧 Repairs
- **View Repairs**: List all submitted repair requests with status
- **Create Repair**: Submit new repair request with description and location

#### 🔍 Lost & Found
- **View Items**: See all lost/found items reported
- **Report Item**: Report LOST or FOUND item with details

---

## 👔 STAFF CLI

### Usage
```bash
python manage.py staff_cli staff1
```

### Dashboard Menu
```
╔═══════════════════════════════════════════════════════════════╗
║                    STAFF DASHBOARD                            ║
╚═══════════════════════════════════════════════════════════════╝

[1] Announcements
[2] Packages
[3] Bookings
[4] Repairs
[5] Lost & Found
[0] Logout
```

### Features

#### 📢 Announcements
- **View Announcements**: List all announcements created
- **Create Announcement**: 
  - Enter title & content
  - Select category (GENERAL, EMERGENCY, MAINTENANCE, EVENTS, POLICIES)
  - Automatically sends LINE Flex message to all residents with LINE connected
  - EMERGENCY category uses red header (#dc2626)

#### 📦 Packages
- **View All Packages**: See all packages in system with recipient info
- **Register Package**: 
  - Select resident
  - Enter sender name
  - Automatically sends LINE notification to resident if LINE connected

#### 📅 Bookings
- **View All Bookings**: Display all facility bookings across all residents

#### 🔧 Repairs
- **View All Repairs**: See all repair requests in the system
- **Assign Maintenance**: Assign PENDING maintenance requests to available technicians
- **Handle Complaint (Self)**: Assign PENDING complaint requests to yourself and update status

#### 🔍 Lost & Found
- **View Items**: Display all lost/found reports
- **Approve Item**: Approve pending items to make them visible to residents
- **Mark Resolved**: Update item status to RESOLVED and assign resolver

---

## 🔧 TECHNICIAN CLI

### Usage
```bash
python manage.py technician_cli tech1
```

### Dashboard Menu
## 🔧 TECHNICIAN CLI

### Usage
```bash
python manage.py technician_cli tech1
```

### Dashboard Menu
```
╔═══════════════════════════════════════════════════════════════╗
║                  TECHNICIAN DASHBOARD                         ║
╚════════════════════════════════════════════════════════════════╝

📊 Status: PENDING (3) | IN PROCESS (2)

[1] View Assigned Repairs
[2] Manage Repair
[3] Work History
[0] Logout
```

### Features

#### 🔧 Repair Management
- **View Assigned Repairs**: Display only repairs assigned to you
  - Shows: ID, Resident, Location, Status, Created date

- **Manage Repair**: 
  - View repair details (resident, location, description, logs)
  - Change status:
    - PENDING → ON_PROCESS
    - ON_PROCESS → COMPLETED
    - Any → CANCELLED
  - View work logs history
  - Set rating (1-5 stars) for completed repairs

- **Work History**:
  - View completed jobs with filters (date range, type, rating)
  - Summary stats: total completed, completed this month, average rating
  - List: ID, type, location, rating, completed date

---

## 👨‍⚖️ JURISTIC CLI (Manager/Administrator)

### Usage
```bash
python manage.py juristic_cli staff1
```

### Dashboard Menu
```
╔═══════════════════════════════════════════════════════════════╗
║                  JURISTIC DASHBOARD                           ║
╚═══════════════════════════════════════════════════════════════╝

📊 Outstanding Repairs: PENDING (2) | IN PROCESS (1)

[1] View Pending Requests
[2] Confirm Request
[0] Logout
```

### Features

#### 📋 Pending Request Management
- **View Pending Requests**: Display all PENDING repair requests with:
  - Job ID
  - Request Type (Maintenance/Complaint)
  - Description
  - Resident name
  - Status: "Waiting for confirmation"

- **Confirm Request**: 
  - View all pending requests
  - Enter Job ID to confirm
  - Select technician from available list
  - System assigns job to technician
  - Job status changes to ON_PROCESS
  - Display confirmation message: "System assigned job #{ID} to {Technician Name}"

---

## 🎨 Output Format Examples

### Booking List
```
╔════════════════════════════════════════════════════════════════╗
║                    📅 BOOKING LIST                             ║
╚════════════════════════════════════════════════════════════════╝

ID     FACILITY             DATE         TIME         STATUS
---------|--------|--------|--------|--------|--------|------
6      Swimming Pool       2026-02-14   17:00-18:00  🟢 CONFIRMED
5      Swimming Pool       2026-02-15   09:00-10:00  🔴 CANCELLED
...
```

### Status Icons
- 🟡 **PENDING** - Waiting for action
- 🟢 **CONFIRMED** - Approved
- 🔴 **CANCELLED** - Cancelled
- ⚪ **EXPIRED** - Expired
- 🔵 **ON_PROCESS** - In progress
- ✅ **COMPLETED** - Done

---

## 💾 Data Persistence

All CLI actions directly modify the database:
- Bookings are saved to facilities_booking
- Packages are recorded in packages_package
- Repairs assigned to technician with status update
- Work logs stored with timestamp
- Announcements broadcast via LINE API

---

## 🔐 Access Control

- **Username validation**: Must be valid user in system
- **Role verification**: User must have corresponding role (Resident/Staff/Technician)
- **Ownership checking**: Residents can only see/modify their own data
- **Assignment checking**: Technicians can only view repairs assigned to them

---

## 🔗 LINE Integration

The CLI system integrates with LINE Messaging API:

### Announcement Broadcasting
When staff creates announcement:
```
╔════════════════════════════════════════════════╗
║        📢 Urgent Announcement                  ║
╠════════════════════════════════════════════════╣
║  Water Maintenance Notice                      ║
║  ┌────────────────────────────────────────┐   ║
║  │ Water will be shut down tomorrow       │   ║
║  │ from 2-4 PM in Building A & B          │   ║
║  └────────────────────────────────────────┘   ║
║  [Read Full Notice]                            ║
╚════════════════════════════════════════════════╝
```

### Package Notification
When staff registers package:
```
╔════════════════════════════════════════════════╗
║     📦 New Package Arrived!                    ║
╠════════════════════════════════════════════════╣
║  From: Amazon Thailand                         ║
║  Package ID: #45                               ║
║  Location: Room 318                            ║
║  [View Details]                                ║
╚════════════════════════════════════════════════╝
```

---

## ⚙️ Technical Details

### Architecture
- **Framework**: Django management commands
- **Database**: SQLite3
- **Input Handling**: `input()` function with validation
- **Display**: Formatted ASCII tables with icons
- **Screen Management**: `os.sy

╔════════════════════════════════════════════════════════════════╗
║                  RESIDENT CLI - LOGIN                          ║
╚════════════════════════════════════════════════════════════════╝

Username: aomnaiiii
Password: ••••••••
)` for Windows, `clear` for Unix

### Key Components
1. **BaseCommand class**: Django management command interface
2. **Dashboard loop**: While True loop for menu navigation
3. **Data validation**: Try-except for error handling
4. **Formatted output**: ASCII box drawing for visual appeal

### Files Created
```
users/management/commands/
├── resident_cli.py      (453 lines)
├── staff_cli.py         (515 lines)
├── technician_cli.py    (348 lines)
├── juristic_cli.py      (239 lines)
└── __init__.py
```

---

## 🚀 Usage Examples

### Example 1: Resident Books Facility
```bash
$ python manage.py resident_cli aomnaiiii

Welcome aomnaiiii (418)

╔═══════════════════════════════════════════════════════════════╗
║                    RESIDENT DASHBOARD                         ║
╚═══════════════════════════════════════════════════════════════╝

[1] View Bookings
[2] Manage Bookings
[3] View Packages
[4] Manage Repairs
[5] Lost & Found
[0] Logout

Select: 2
--------------------------------------------------
[1] Swimming Pool (Capacity: 50)
[2] Fitness Gym (Capacity: 30)
[3] Meeting Room (Capacity: 20)

Select Facility ID: 1
Enter Date (YYYY-MM-DD): 2026-02-20
Enter Time Slot (HH:MM-HH:MM): 09:00-11:00

✅ Booking created successfully!
   Booking ID: 7
   Facility: Swimming Pool
   Date: 2026-02-20
   Time: 09:00-11:00
```

### Example 2: Staff Creates Announcement
```bash
$ python manage.py staff_cli staff1

[1] Announcements
Select: 1

[1] View Announcements
[2] Create Announcement
Select: 2

Enter Title: Emergency Maintenance Alert
Enter Content: Power outage in Building A from 2-4 PM

[1] GENERAL

╔════════════════════════════════════════════════════════════════╗
║                JURISTIC CLI - LOGIN                            ║
╚════════════════════════════════════════════════════════════════╝

Username: staff1
Password: ••••••••
[2] EMERGENCY
[3] MAINTENANCE
[4] EVENTS
[5] POLICIES
Select Category (1-5): 2

Announcement created successfully!
   ID: 8
   Category: EMERGENCY
   Sent to 15 residents via LINE
```

### Example 3: Juristic Confirms Repair
```bash
$ python manage.py juristic_cli staff1

[1] View Pending Requests
[2] Confirm Request
Select: 2

=== PENDING REQUESTS ===

[1] Maintenance Job
Job ID        : 1
Category      : Maintenance
De**Login Required**: All CLI interfaces require valid username/password (same as web login)
- **Login Attempts**: Maximum 3 failed login attempts allowed
- **Password Display**: Password input is hidden while typing
- **Case Sensitive**: Username and password are case-sensitive
- **Role Validation**: User must have correct role for selected CLI (Resident, Staff, Technician)
- **Dashboard Loop**: Once logged in, CLI loops until user logs out ([0] Logout)
- **Screen Clearing**: Screen clears between menu transitions for clean UX
- **Timestamps**: All timestamps stored in database with timezone awareness
- **LINE Integration**: LINE notifications require resident to have line_user_id connected
- **Status Updates**:--

Enter Job ID to confirm: 1

👨‍🔧 SELECT TECHNICIAN:
--------------------------------------------------
[1] Mr. Anan ✅
[2] Mr. Somchai 🔴

Select Technician (number): 1

✅ System assigned job #1 to Mr. Anan
```
Login failed - Invalid username or password | Check username and password spelling, verify user exists in database |
| Login failed - Too many attempts | Wait and try again later, or reset password via web interface |
| User is not [role] | Use correct CLI for user's role (Resident CLI for residents, staff CLI for staff, etc.) |
| Invalid choice | Enter number from menu exactly as shown |
| Invalid date format | Use YYYY-MM-DD format for dates |
| Resident not found | Verify resident ID in database |
| Authentication failed | Ensure Django authentication backend is configured correctly
- All CLI interfaces loop until user logs out ([0] Logout)
- Screen clears between menu transitions for clean UX
- All timestamps are stored in database with timezone awareness
- LINE notifications require resident to have line_user_id connected
- Repair assignments automatically change status from PENDING to ON_PROCESS

---

## 🐛 Error Handling

Common issues and solutions:

| Issue | Solution |
|-------|----------|
| User does not exist | Check username spelling and verify user in Django admin |
| User is not [role] | Use correct CLI for user's role |
| Invalid choice | Enter number from menu exactly as shown |
| Invalid date format | Use YYYY-MM-DD format for dates |
| Resident not found | Verify resident ID in database |

---

## 📞 Support

For issues or enhancements, contact development team.

**Last Updated**: February 14, 2026  
**Version**: 1.0  
**Status**: Production Ready ✅
