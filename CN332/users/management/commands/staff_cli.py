from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import authenticate
from datetime import datetime
from users.models import User, Staff, Resident, Technician
from facilities.models import Booking
from packages.models import Package
from announcements.models import Announcement
from repairs.models import RepairRequest, WorkLog
from lost_found.models import LostFound
from users.services.line_messaging import send_line_flex_message
import os
import getpass


class Command(BaseCommand):
    help = 'Interactive CLI dashboard for Staff'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the staff member')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found")
        
        try:
            staff = user.staff
        except Staff.DoesNotExist:
            raise CommandError(f"User {username} is not a staff member")

        self.run_dashboard(staff, user)



    def run_dashboard(self, staff, user):
        """Main dashboard loop"""
        while True:
            self.clear_screen()
            self.print_header(f"Welcome {user.first_name or user.username} ({staff.position})")
            self.print_dashboard_menu()
            
            choice = input("\nSelect: ").strip()
            
            if choice == '1':
                self.announcements_menu(staff)
            elif choice == '2':
                self.packages_menu(staff)
            elif choice == '3':
                self.bookings_menu()
            elif choice == '4':
                self.repairs_menu(staff)
            elif choice == '5':
                self.lost_found_menu(staff)
            elif choice == '0':
                self.stdout.write(self.style.SUCCESS("Goodbye!"))
                break
            else:
                input("\n❌ Invalid choice. Press Enter to continue...")

    def print_dashboard_menu(self):
        menu = """
╔═══════════════════════════════════════════════════════════════╗
║                    STAFF DASHBOARD                            ║
╚═══════════════════════════════════════════════════════════════╝

[1] Announcements
[2] Packages
[3] Bookings
[4] Repairs
[5] Lost & Found
[0] Logout
"""
        print(menu)

    def announcements_menu(self, staff):
        while True:
            self.clear_screen()
            self.print_header("📢 ANNOUNCEMENTS")
            
            menu = """
[1] View Announcements
[2] Create Announcement
[0] Back
"""
            print(menu)
            
            choice = input("Select: ").strip()
            
            if choice == '1':
                self.view_announcements(staff)
            elif choice == '2':
                self.create_announcement(staff)
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")

    def view_announcements(self, staff):
        self.clear_screen()
        self.print_header("📢 ANNOUNCEMENT LIST")
        
        announcements = Announcement.objects.filter(author=staff).order_by('-publish_date')
        
        if not announcements:
            print("\n❌ No announcements found")
        else:
            print("\n{:<6} {:<25} {:<15} {:<20}".format(
                "ID", "TITLE", "CATEGORY", "PUBLISHED"
            ))
            print("-" * 75)
            
            for ann in announcements:
                category_icon = '🔴' if ann.category == 'EMERGENCY' else '📌'
                published = ann.publish_date.strftime("%Y-%m-%d %H:%M")
                
                print("{:<6} {:<25} {:<2} {:<12} {:<20}".format(
                    ann.id,
                    ann.title[:23],
                    category_icon,
                    ann.category,
                    published
                ))
        
        input("\nPress Enter to continue...")

    def create_announcement(self, staff):
        self.clear_screen()
        self.print_header("➕ CREATE ANNOUNCEMENT")
        
        try:
            title = input("\nEnter Title: ")
            content = input("Enter Content: ")
            
            print("\n[1] GENERAL")
            print("[2] EMERGENCY")
            print("[3] MAINTENANCE")
            print("[4] EVENTS")
            print("[5] POLICIES")
            category_choice = input("Select Category (1-5): ")
            
            category_map = {
                '1': 'GENERAL',
                '2': 'EMERGENCY',
                '3': 'MAINTENANCE',
                '4': 'EVENTS',
                '5': 'POLICIES',
            }
            category = category_map.get(category_choice, 'GENERAL')
            
            if not title or not content:
                print("\n❌ Title and content are required")
                input("Press Enter to continue...")
                return
            
            announcement = Announcement.objects.create(
                title=title,
                content=content,
                category=category,
                author=staff
            )
            
            # Send to all residents with LINE connected
            residents_with_line = Resident.objects.filter(
                user__line_user_id__isnull=False
            ).exclude(user__line_user_id='')
            
            success_count = 0
            for resident in residents_with_line:
                try:
                    header_color = '#dc2626' if category == 'EMERGENCY' else '#ef4444'
                    title_text = 'Urgent Announcement' if category == 'EMERGENCY' else 'New Announcement'
                    
                    flex_json = {
                        "type": "bubble",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": header_color,
                            "contents": [{
                                "type": "text",
                                "text": title_text,
                                "color": "#ffffff",
                                "weight": "bold",
                                "size": "lg"
                            }]
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "md",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": announcement.title,
                                    "weight": "bold",
                                    "size": "md"
                                },
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "margin": "md",
                                    "spacing": "sm",
                                    "backgroundColor": "#fecaca",
                                    "paddingAll": "12px",
                                    "borderRadius": "8px",
                                    "contents": [{
                                        "type": "text",
                                        "text": announcement.content[:100] + ('...' if len(announcement.content) > 100 else ''),
                                        "size": "sm",
                                        "color": "#991b1b",
                                        "wrap": True
                                    }]
                                }
                            ]
                        }
                    }
                    
                    send_line_flex_message(
                        resident.user.line_user_id,
                        announcement.title,
                        flex_json
                    )
                    success_count += 1
                except Exception as e:
                    pass
            
            print(f"\n✅ Announcement created successfully!")
            print(f"   ID: {announcement.id}")
            print(f"   Category: {category}")
            print(f"   Sent to {success_count} residents via LINE")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def packages_menu(self, staff):
        while True:
            self.clear_screen()
            self.print_header("📦 PACKAGES")
            
            menu = """
[1] View All Packages
[2] Register New Package
[0] Back
"""
            print(menu)
            
            choice = input("Select: ").strip()
            
            if choice == '1':
                self.view_all_packages()
            elif choice == '2':
                self.register_package(staff)
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")

    def view_all_packages(self):
        self.clear_screen()
        self.print_header("📦 PACKAGE LIST")
        
        packages = Package.objects.all().order_by('-arrived_at')
        
        if not packages:
            print("\n❌ No packages found")
        else:
            print("\n{:<6} {:<20} {:<18} {:<12} {:<15}".format(
                "ID", "RECIPIENT", "FROM", "STATUS", "ARRIVED"
            ))
            print("-" * 80)
            
            for pkg in packages:
                status_icon = '🟡' if pkg.status == 'RECEIVED' else '✅'
                arrived = pkg.arrived_at.strftime("%Y-%m-%d %H:%M")
                
                print("{:<6} {:<20} {:<18} {:<2} {:<9} {:<15}".format(
                    pkg.id,
                    pkg.resident.user.username[:18],
                    pkg.sender[:16],
                    status_icon,
                    pkg.status,
                    arrived
                ))
        
        input("\nPress Enter to continue...")

    def register_package(self, staff):
        self.clear_screen()
        self.print_header("➕ REGISTER NEW PACKAGE")
        
        try:
            # Show residents
            residents = Resident.objects.all()
            if not residents:
                print("\n❌ No residents found")
                input("Press Enter to continue...")
                return
            
            print("\n👥 SELECT RECIPIENT:")
            print("-" * 50)
            for res in residents[:10]:
                print(f"[{res.id}] {res.user.username} ({res.room_number})")
            if residents.count() > 10:
                print(f"... and {residents.count() - 10} more")
            
            resident_id = int(input("\nEnter Resident ID: "))
            resident = Resident.objects.get(id=resident_id)
            
            sender = input("Enter Sender Name: ")
            
            if not sender:
                print("\n❌ Sender name is required")
                input("Press Enter to continue...")
                return
            
            package = Package.objects.create(
                resident=resident,
                sender=sender,
                handled_by=staff,
                status='RECEIVED'
            )
            
            # Send LINE notification
            if resident.user.line_user_id:
                try:
                    flex_json = {
                        "type": "bubble",
                        "header": {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#22c55e",
                            "contents": [{
                                "type": "text",
                                "text": "📦 New Package Arrived!",
                                "color": "#ffffff",
                                "weight": "bold",
                                "size": "lg"
                            }]
                        },
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "md",
                            "contents": [
                                {"type": "text", "text": f"From: {sender}", "weight": "bold"},
                                {"type": "text", "text": f"Package ID: #{package.id}"},
                                {"type": "text", "text": f"Location: {resident.room_number}", "size": "sm", "color": "#666666"}
                            ]
                        }
                    }
                    
                    send_line_flex_message(
                        resident.user.line_user_id,
                        f"Package from {sender}",
                        flex_json
                    )
                except:
                    pass
            
            print(f"\n✅ Package registered successfully!")
            print(f"   Package ID: {package.id}")
            print(f"   Recipient: {resident.user.username} ({resident.room_number})")
            print(f"   Sender: {sender}")
            
        except ValueError:
            print("\n❌ Invalid input")
        except Resident.DoesNotExist:
            print("\n❌ Resident not found")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def bookings_menu(self):
        self.clear_screen()
        self.print_header("📅 BOOKINGS")
        
        bookings = Booking.objects.all().order_by('-created_at')
        
        if not bookings:
            print("\n❌ No bookings found")
        else:
            print("\n{:<6} {:<20} {:<18} {:<12} {:<12} {:<12}".format(
                "ID", "RESIDENT", "FACILITY", "DATE", "TIME", "STATUS"
            ))
            print("-" * 85)
            
            for booking in bookings:
                status_icon = {
                    'PENDING': '🟡',
                    'CONFIRMED': '🟢',
                    'CANCELLED': '🔴',
                    'EXPIRED': '⚪',
                }.get(booking.status, '?')
                
                print("{:<6} {:<20} {:<18} {:<12} {:<12} {:<2} {}".format(
                    booking.id,
                    booking.resident.user.username[:18],
                    booking.facility.name[:16],
                    str(booking.booking_date),
                    booking.time_slot,
                    status_icon,
                    booking.status
                ))
        
        input("\nPress Enter to continue...")

    def repairs_menu(self, staff):
        while True:
            self.clear_screen()
            self.print_header("🔧 REPAIRS")

            menu = """
[1] View Repairs
[2] Assign Maintenance to Technician
[3] Handle Complaint (Assign to Self)
[0] Back
"""
            print(menu)

            choice = input("Select: ").strip()

            if choice == '1':
                self.view_repairs_list()
            elif choice == '2':
                self.assign_maintenance_to_technician()
            elif choice == '3':
                self.handle_complaint_self(staff)
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")

    def view_repairs_list(self):
        self.clear_screen()
        self.print_header("🔧 REPAIRS")

        repairs = RepairRequest.objects.all().order_by('-created_at')

        if not repairs:
            print("\n❌ No repair requests found")
        else:
            print("\n{:<6} {:<12} {:<18} {:<12} {:<20}".format(
                "ID", "TYPE", "LOCATION", "STATUS", "CREATED"
            ))
            print("-" * 75)

            for repair in repairs:
                status_icon = {
                    'PENDING': '🟡',
                    'ON_PROCESS': '🔵',
                    'COMPLETED': '✅',
                    'CANCELLED': '❌',
                }.get(repair.status, '?')

                created = repair.created_at.strftime("%Y-%m-%d %H:%M")

                print("{:<6} {:<12} {:<18} {:<2} {:<9} {:<20}".format(
                    repair.id,
                    repair.request_type,
                    repair.location[:16],
                    status_icon,
                    repair.status,
                    created
                ))

        input("\nPress Enter to continue...")

    def assign_maintenance_to_technician(self):
        self.clear_screen()
        self.print_header("🔧 ASSIGN MAINTENANCE")

        repairs = RepairRequest.objects.filter(
            request_type='MAINTENANCE',
            status='PENDING'
        ).order_by('-created_at')

        if not repairs:
            print("\n❌ No pending maintenance requests")
            input("Press Enter to continue...")
            return

        print("\nPending Maintenance Requests:")
        print("-" * 65)
        for repair in repairs:
            print(f"ID: {repair.id} | {repair.location} | {repair.resident.user.username}")

        try:
            repair_id = int(input("\nEnter Repair ID to assign: "))
            repair = RepairRequest.objects.get(id=repair_id, status='PENDING', request_type='MAINTENANCE')

            technicians = Technician.objects.filter(availability='AVAILABLE')
            if not technicians:
                print("\n❌ No available technicians")
                input("Press Enter to continue...")
                return

            print("\n👨‍🔧 SELECT TECHNICIAN:")
            print("-" * 50)
            tech_list = []
            for idx, tech in enumerate(technicians, 1):
                print(f"[{idx}] {tech.user.first_name} {tech.user.last_name}")
                tech_list.append(tech)

            tech_choice = int(input("\nSelect Technician (number): "))
            technician = tech_list[tech_choice - 1]

            repair.technician = technician
            repair.status = 'ON_PROCESS'
            repair.save()

            WorkLog.objects.create(
                repair_request=repair,
                description=f"Assigned to technician: {technician.user.username}"
            )

            print(f"\n✅ Assigned repair #{repair.id} to {technician.user.first_name} {technician.user.last_name}")

        except ValueError:
            print("\n❌ Invalid input")
        except (RepairRequest.DoesNotExist, IndexError):
            print("\n❌ Repair or technician not found")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

        input("\nPress Enter to continue...")

    def handle_complaint_self(self, staff):
        self.clear_screen()
        self.print_header("🧾 HANDLE COMPLAINT")

        repairs = RepairRequest.objects.filter(
            request_type='COMPLAINT',
            status__in=['PENDING', 'ON_PROCESS']
        ).order_by('-created_at')

        if not repairs:
            print("\n❌ No pending complaints")
            input("Press Enter to continue...")
            return

        print("\nComplaints (Pending / In Process):")
        print("-" * 65)
        for repair in repairs:
            owner = repair.assigned_staff.user.username if repair.assigned_staff else "-"
            print(f"ID: {repair.id} | {repair.location} | {repair.resident.user.username} | {repair.status} | Staff: {owner}")

        try:
            repair_id = int(input("\nEnter Complaint ID to handle: "))
            repair = RepairRequest.objects.get(id=repair_id, request_type='COMPLAINT')

            if repair.status not in ['PENDING', 'ON_PROCESS']:
                print("\n❌ This complaint cannot be handled in its current status")
                input("Press Enter to continue...")
                return

            if repair.assigned_staff and repair.assigned_staff != staff:
                print("\n❌ This complaint is already assigned to another staff")
                input("Press Enter to continue...")
                return

            if not repair.assigned_staff:
                repair.assigned_staff = staff
                repair.status = 'ON_PROCESS'
                repair.save()

                WorkLog.objects.create(
                    repair_request=repair,
                    description=f"Assigned to staff: {staff.user.username}"
                )

            print("\n[1] Keep status ON_PROCESS")
            print("[2] Mark COMPLETED")
            print("[3] Mark CANCELLED")
            status_choice = input("Select: ").strip() or '1'

            status_map = {
                '1': 'ON_PROCESS',
                '2': 'COMPLETED',
                '3': 'CANCELLED',
            }
            new_status = status_map.get(status_choice, 'ON_PROCESS')

            work_note = input("\nOptional work note: ").strip()
            if work_note:
                WorkLog.objects.create(
                    repair_request=repair,
                    description=work_note
                )

            if new_status != repair.status:
                repair.status = new_status
                repair.save()
                WorkLog.objects.create(
                    repair_request=repair,
                    description=f"Status updated to: {repair.get_status_display()}"
                )

            print(f"\n✅ Complaint #{repair.id} assigned to {staff.user.username} and set to {repair.status}")

        except ValueError:
            print("\n❌ Invalid input")
        except RepairRequest.DoesNotExist:
            print("\n❌ Complaint not found")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

        input("\nPress Enter to continue...")

    def lost_found_menu(self, staff):
        while True:
            self.clear_screen()
            self.print_header("🔍 LOST & FOUND")

            menu = """
[1] View Items
[2] Approve Item
[3] Mark Resolved
[0] Back
"""
            print(menu)

            choice = input("Select: ").strip()

            if choice == '1':
                self.view_lost_found_items()
            elif choice == '2':
                self.approve_lost_found_item()
            elif choice == '3':
                self.resolve_lost_found_item(staff)
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")

    def view_lost_found_items(self):
        self.clear_screen()
        self.print_header("🔍 LOST & FOUND ITEMS")

        items = LostFound.objects.all().order_by('-reported_at')

        if not items:
            print("\n❌ No items found")
        else:
            print("\n{:<6} {:<18} {:<12} {:<10} {:<10} {:<10} {:<15}".format(
                "ID", "ITEM", "REPORTER", "TYPE", "STATUS", "APPROVED", "REPORTED"
            ))
            print("-" * 90)

            for item in items:
                reported = item.reported_at.strftime("%Y-%m-%d %H:%M")
                approved_text = 'YES' if item.is_approved else 'NO'

                print("{:<6} {:<18} {:<12} {:<10} {:<10} {:<10} {:<15}".format(
                    item.id,
                    item.item_name[:16],
                    item.reporter.user.username[:10],
                    item.item_type,
                    item.status,
                    approved_text,
                    reported
                ))

        input("\nPress Enter to continue...")

    def approve_lost_found_item(self):
        self.clear_screen()
        self.print_header("✅ APPROVE LOST & FOUND")

        items = LostFound.objects.filter(is_approved=False).order_by('-reported_at')

        if not items:
            print("\n❌ No items pending approval")
            input("Press Enter to continue...")
            return

        print("\nPending Approval:")
        print("-" * 65)
        for item in items:
            print(f"ID: {item.id} | {item.item_name} | {item.item_type} | {item.status}")

        try:
            item_id = int(input("\nEnter Item ID to approve: "))
            item = LostFound.objects.get(id=item_id, is_approved=False)
            item.is_approved = True
            item.save()
            print(f"\n✅ Approved item #{item.id} ({item.item_name})")
        except ValueError:
            print("\n❌ Invalid input")
        except LostFound.DoesNotExist:
            print("\n❌ Item not found or already approved")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

        input("\nPress Enter to continue...")

    def resolve_lost_found_item(self, staff):
        self.clear_screen()
        self.print_header("✅ MARK RESOLVED")

        items = LostFound.objects.exclude(status='RESOLVED').order_by('-reported_at')

        if not items:
            print("\n❌ No items to resolve")
            input("Press Enter to continue...")
            return

        print("\nUnresolved Items:")
        print("-" * 65)
        for item in items:
            print(f"ID: {item.id} | {item.item_name} | {item.item_type} | {item.status}")

        try:
            item_id = int(input("\nEnter Item ID to resolve: "))
            item = LostFound.objects.get(id=item_id)
            if item.status == 'RESOLVED':
                print("\n❌ Item already resolved")
                input("Press Enter to continue...")
                return

            item.status = 'RESOLVED'
            item.resolver = staff
            item.save()
            print(f"\n✅ Resolved item #{item.id} ({item.item_name})")
        except ValueError:
            print("\n❌ Invalid input")
        except LostFound.DoesNotExist:
            print("\n❌ Item not found")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

        input("\nPress Enter to continue...")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title):
        print("╔════════════════════════════════════════════════════════════════╗")
        print(f"║ {title:<62} ║")
        print("╚════════════════════════════════════════════════════════════════╝")
