from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import models
from datetime import datetime
from users.models import User, Resident
from facilities.models import Booking, Facility
from packages.models import Package
from repairs.models import RepairRequest
from lost_found.models import LostFound
from announcements.models import Announcement
import os
import sys


class Command(BaseCommand):
    help = 'Interactive CLI dashboard for Residents'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the resident')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found")
        
        try:
            resident = user.resident
        except Resident.DoesNotExist:
            raise CommandError(f"User {username} is not a resident")

        self.run_dashboard(resident, user)



    def run_dashboard(self, resident, user):
        """Main dashboard loop"""
        while True:
            self.clear_screen()
            self.print_header(f"Welcome {user.first_name or user.username} ({resident.room_number})")
            self.print_dashboard_menu()
            
            choice = input("\nSelect: ").strip()
            
            if choice == '1':
                self.view_bookings(resident)
            elif choice == '2':
                self.bookings_menu(resident)
            elif choice == '3':
                self.view_packages(resident)
            elif choice == '4':
                self.repairs_menu(resident)
            elif choice == '5':
                self.lost_found_menu(resident)
            elif choice == '6':
                self.view_announcements()
            elif choice == '0':
                self.stdout.write(self.style.SUCCESS("Goodbye!"))
                break
            else:
                input("\n❌ Invalid choice. Press Enter to continue...")

    def print_dashboard_menu(self):
        menu = """
╔═══════════════════════════════════════════════════════════════╗
║                    RESIDENT DASHBOARD                         ║
╚═══════════════════════════════════════════════════════════════╝

[1] View Bookings
[2] Manage Bookings
[3] View Packages
[4] Manage Repairs
[5] Lost & Found
[6] View Announcements
[0] Logout
"""
        print(menu)

    def view_bookings(self, resident):
        self.clear_screen()
        self.print_header("📅 BOOKING LIST")
        
        bookings = Booking.objects.filter(resident=resident).order_by('-created_at')
        
        if not bookings:
            print("\n❌ No bookings found")
        else:
            print("\n{:<6} {:<20} {:<12} {:<12} {:<12}".format(
                "ID", "FACILITY", "DATE", "TIME", "STATUS"
            ))
            print("-" * 70)
            
            for booking in bookings:
                status_color = {
                    'PENDING': '🟡',
                    'CONFIRMED': '🟢',
                    'CANCELLED': '🔴',
                    'EXPIRED': '⚪',
                }.get(booking.status, '')
                
                print("{:<6} {:<20} {:<12} {:<12} {:<2} {}".format(
                    booking.id,
                    booking.facility.name[:18],
                    str(booking.booking_date),
                    booking.time_slot,
                    status_color,
                    booking.status
                ))
        
        input("\nPress Enter to continue...")

    def bookings_menu(self, resident):
        while True:
            self.clear_screen()
            self.print_header("📅 MANAGE BOOKINGS")
            
            menu = """
[1] Create Booking
[2] Cancel Booking
[0] Back
"""
            print(menu)
            
            choice = input("Select: ").strip()
            
            if choice == '1':
                self.create_booking(resident)
            elif choice == '2':
                self.cancel_booking(resident)
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")

    def create_booking(self, resident):
        self.clear_screen()
        self.print_header("➕ CREATE BOOKING")
        
        try:
            # Show available facilities
            facilities = Facility.objects.filter(is_open=True)
            if not facilities:
                print("\n❌ No facilities available")
                input("Press Enter to continue...")
                return
            
            print("\n📋 AVAILABLE FACILITIES:")
            print("-" * 50)
            for fac in facilities:
                print(f"[{fac.id}] {fac.name} (Capacity: {fac.capacity})")
            
            facility_id = int(input("\nSelect Facility ID: "))
            facility = Facility.objects.get(id=facility_id, is_open=True)
            
            booking_date_str = input("Enter Date (YYYY-MM-DD): ")
            booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
            
            time_slot = input("Enter Time Slot (HH:MM-HH:MM): ")
            
            # Check existing booking
            existing = Booking.objects.filter(
                facility=facility,
                booking_date=booking_date,
                time_slot=time_slot,
                status__in=['PENDING', 'CONFIRMED']
            )
            
            if existing:
                print("\n❌ Facility already booked for this time")
                input("Press Enter to continue...")
                return
            
            booking = Booking.objects.create(
                resident=resident,
                facility=facility,
                booking_date=booking_date,
                time_slot=time_slot,
                status='CONFIRMED'
            )
            
            print(f"\n✅ Booking created successfully!")
            print(f"   Booking ID: {booking.id}")
            print(f"   Facility: {facility.name}")
            print(f"   Date: {booking_date}")
            print(f"   Time: {time_slot}")
            
        except ValueError as e:
            print(f"\n❌ Invalid input: {str(e)}")
        except Facility.DoesNotExist:
            print("\n❌ Facility not found")
        
        input("\nPress Enter to continue...")

    def cancel_booking(self, resident):
        self.clear_screen()
        self.print_header("❌ CANCEL BOOKING")
        
        # Display all bookings first
        bookings = Booking.objects.filter(resident=resident).order_by('-created_at')
        
        if not bookings.exists():
            print("\n❌ You have no bookings to cancel")
            input("Press Enter to continue...")
            return
        
        print("\n📋 YOUR BOOKINGS:")
        print("-" * 80)
        print(f"{'ID':<5} {'FACILITY':<20} {'DATE':<12} {'TIME':<15} {'STATUS':<12}")
        print("-" * 80)
        
        for booking in bookings:
            status_icon = {
                'PENDING': '🟡',
                'CONFIRMED': '🟢',
                'CANCELLED': '🔴',
                'EXPIRED': '⚪',
            }.get(booking.status, '')
            print(f"{booking.id:<5} {booking.facility.name[:18]:<20} {str(booking.booking_date):<12} {booking.time_slot:<15} {status_icon} {booking.status:<10}")
        
        print("-" * 80)
        
        try:
            booking_id = int(input("\nEnter Booking ID to cancel: "))
            booking = Booking.objects.get(id=booking_id, resident=resident)
            
            if booking.status in ['CANCELLED', 'EXPIRED']:
                print(f"\n❌ Cannot cancel booking with status {booking.status}")
                input("Press Enter to continue...")
                return
            
            confirm = input(f"\nConfirm cancel booking #{booking_id}? (y/n): ").lower()
            if confirm != 'y':
                print("Cancelled")
                input("Press Enter to continue...")
                return
            
            booking.status = 'CANCELLED'
            booking.save()
            
            print(f"\n✅ Booking #{booking_id} cancelled successfully!")
            
        except ValueError:
            print("\n❌ Invalid booking ID")
        except Booking.DoesNotExist:
            print("\n❌ Booking not found")
        
        input("Press Enter to continue...")

    def view_packages(self, resident):
        self.clear_screen()
        self.print_header("📦 PACKAGE LIST")
        
        packages = Package.objects.filter(resident=resident).order_by('-arrived_at')
        
        if not packages:
            print("\n❌ No packages found")
        else:
            print("\n{:<6} {:<20} {:<12} {:<20}".format(
                "ID", "FROM", "STATUS", "ARRIVED"
            ))
            print("-" * 65)
            
            for pkg in packages:
                status_icon = '🟡' if pkg.status == 'RECEIVED' else '✅'
                arrived_time = pkg.arrived_at.strftime("%Y-%m-%d %H:%M")
                
                print("{:<6} {:<20} {:<2} {:<9} {:<20}".format(
                    pkg.id,
                    pkg.sender[:18],
                    status_icon,
                    pkg.status,
                    arrived_time
                ))
        
        input("\nPress Enter to continue...")

    def repairs_menu(self, resident):
        while True:
            self.clear_screen()
            self.print_header("🔧 REPAIR MANAGEMENT")
            
            menu = """
[1] View Repairs
[2] Create Repair Request
[0] Back
"""
            print(menu)
            
            choice = input("Select: ").strip()
            
            if choice == '1':
                self.view_repairs(resident)
            elif choice == '2':
                self.create_repair(resident)
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")

    def view_repairs(self, resident):
        self.clear_screen()
        self.print_header("🔧 REPAIR REQUESTS")
        
        repairs = RepairRequest.objects.filter(resident=resident).order_by('-created_at')
        
        if not repairs:
            print("\n❌ No repair requests found")
        else:
            print("\n{:<6} {:<20} {:<12} {:<20}".format(
                "ID", "LOCATION", "STATUS", "CREATED"
            ))
            print("-" * 65)
            
            for repair in repairs:
                status_icon = {
                    'PENDING': '🟡',
                    'ON_PROCESS': '🔵',
                    'COMPLETED': '✅',
                    'CANCELLED': '❌',
                }.get(repair.status, '?')
                
                created = repair.created_at.strftime("%Y-%m-%d %H:%M")
                
                print("{:<6} {:<20} {:<2} {:<8} {:<20}".format(
                    repair.id,
                    repair.location[:18],
                    status_icon,
                    repair.status,
                    created
                ))
        
        input("\nPress Enter to continue...")

    def create_repair(self, resident):
        self.clear_screen()
        self.print_header("➕ CREATE REPAIR REQUEST")
        
        try:
            description = input("\nEnter Description: ")
            location = input("Enter Location: ")
            
            if not description or not location:
                print("\n❌ Description and location are required")
                input("Press Enter to continue...")
                return
            
            repair = RepairRequest.objects.create(
                resident=resident,
                description=description,
                location=location,
                request_type='MAINTENANCE',
                status='PENDING'
            )
            
            print(f"\n✅ Repair request created successfully!")
            print(f"   Request ID: {repair.id}")
            print(f"   Location: {location}")
            print(f"   Status: PENDING")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def lost_found_menu(self, resident):
        while True:
            self.clear_screen()
            self.print_header("🔍 LOST & FOUND")
            
            menu = """
[1] View Lost & Found
[2] Report Lost/Found Item
[0] Back
"""
            print(menu)
            
            choice = input("Select: ").strip()
            
            if choice == '1':
                self.view_lost_found(resident)
            elif choice == '2':
                self.report_lost_found(resident)
            elif choice == '0':
                break
            else:
                print("❌ Invalid choice")
                input("Press Enter to continue...")

    def view_lost_found(self, resident):
        self.clear_screen()
        self.print_header("🔍 LOST & FOUND ITEMS")
        
        items = LostFound.objects.filter(
            models.Q(reporter=resident) | models.Q(claimant=resident)
        ).order_by('-reported_at')
        
        if not items:
            print("\n❌ No items found")
        else:
            print("\n{:<6} {:<15} {:<12} {:<20}".format(
                "ID", "ITEM", "TYPE", "STATUS"
            ))
            print("-" * 50)
            
            for item in items:
                reported = item.reported_at.strftime("%Y-%m-%d %H:%M")
                
                print("{:<6} {:<15} {:<12} {:<20}".format(
                    item.id,
                    item.item_name[:13],
                    item.item_type,
                    item.status
                ))
        
        input("\nPress Enter to continue...")

    def report_lost_found(self, resident):
        self.clear_screen()
        self.print_header("➕ REPORT LOST/FOUND ITEM")
        
        try:
            item_name = input("\nEnter Item Name: ")
            item_desc = input("Enter Description: ")
            item_location = input("Enter Location: ")
            
            print("\n[1] LOST")
            print("[2] FOUND")
            item_type_choice = input("Select Type (1-2): ")
            
            item_type = 'LOST' if item_type_choice == '1' else 'FOUND'
            
            if not all([item_name, item_desc, item_location]):
                print("\n❌ All fields are required")
                input("Press Enter to continue...")
                return
            
            item = LostFound.objects.create(
                reporter=resident,
                item_name=item_name,
                description=item_desc,
                location=item_location,
                item_type=item_type,
                status='PENDING'
            )
            
            print(f"\n✅ Item reported successfully!")
            print(f"   Item ID: {item.id}")
            print(f"   Name: {item_name}")
            print(f"   Type: {item_type}")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def view_announcements(self):
        self.clear_screen()
        self.print_header("📢 ANNOUNCEMENTS")
        
        announcements = Announcement.objects.all().order_by('-publish_date')
        
        if not announcements:
            print("\n❌ No announcements available")
        else:
            for idx, announcement in enumerate(announcements, 1):
                category_icon = {
                    'GENERAL': '📌',
                    'EMERGENCY': '🚨',
                    'MAINTENANCE': '🔧',
                    'EVENTS': '🎉',
                    'POLICIES': '📋',
                }.get(announcement.category, '📌')
                
                pub_date = announcement.publish_date.strftime("%Y-%m-%d %H:%M")
                author_name = announcement.author.user.first_name or announcement.author.user.username if announcement.author else "Unknown"
                
                print(f"\n{'='*70}")
                print(f"{category_icon} [{announcement.category}] {announcement.title}")
                print(f"   By: {author_name} | Published: {pub_date}")
                print(f"{'='*70}")
                print(f"{announcement.content}")
        
        input("\nPress Enter to continue...")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title):
        print("╔════════════════════════════════════════════════════════════════╗")
        print(f"║ {title:<62} ║")
        print("╚════════════════════════════════════════════════════════════════╝")
