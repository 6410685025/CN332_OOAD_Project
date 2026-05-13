from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import models
from users.models import User, Technician
from repairs.models import RepairRequest, WorkLog
from datetime import datetime, timedelta
import os


class Command(BaseCommand):
    help = 'Interactive CLI dashboard for Technicians'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the technician')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found")
        
        try:
            technician = user.technician
        except Technician.DoesNotExist:
            raise CommandError(f"User {user.username} is not a technician")

        self.run_dashboard(technician, user)
    def run_dashboard(self, technician, user):
        """Main dashboard loop"""
        while True:
            self.clear_screen()
            self.print_header(f"Welcome {user.first_name or user.username} (TECHNICIAN)")
            self.print_dashboard_menu(technician)
            
            choice = input("\nSelect: ").strip()
            
            if choice == '1':
                self.view_assigned_repairs(technician)
            elif choice == '2':
                self.manage_repair(technician)
            elif choice == '3':
                self.view_work_history(technician)
            elif choice == '0':
                self.stdout.write(self.style.SUCCESS("Goodbye!"))
                break
            else:
                input("\n❌ Invalid choice. Press Enter to continue...")


    def print_dashboard_menu(self, technician):
        pending_count = RepairRequest.objects.filter(
            technician=technician,
            status='PENDING'
        ).count()
        
        in_process_count = RepairRequest.objects.filter(
            technician=technician,
            status='ON_PROCESS'
        ).count()
        
        menu = """
╔═══════════════════════════════════════════════════════════════╗
║                  TECHNICIAN DASHBOARD                         ║
╚═══════════════════════════════════════════════════════════════╝

"""
        menu += f"📊 Status: PENDING ({pending_count}) | IN PROCESS ({in_process_count})\n"
        menu += """
[1] View Assigned Repairs
[2] Manage Repair
[3] Work History
[0] Logout
"""
        print(menu)

    def view_assigned_repairs(self, technician):
        self.clear_screen()
        self.print_header("🔧 ASSIGNED REPAIRS")
        
        repairs = RepairRequest.objects.filter(
            technician=technician
        ).exclude(status='COMPLETED').order_by('-created_at')
        
        if not repairs:
            print("\n❌ No assigned repairs")
        else:
            print("\n{:<6} {:<15} {:<20} {:<12} {:<18}".format(
                "ID", "RESIDENT", "LOCATION", "STATUS", "CREATED"
            ))
            print("-" * 75)
            
            for repair in repairs:
                status_colors = {
                    'PENDING': '🟡',
                    'ON_PROCESS': '🔵',
                    'COMPLETED': '✅',
                    'CANCELLED': '❌',
                }
                status_icon = status_colors.get(repair.status, '?')
                created = repair.created_at.strftime("%Y-%m-%d %H:%M")
                
                print("{:<6} {:<15} {:<20} {:<2} {:<10} {:<18}".format(
                    repair.id,
                    repair.resident.user.username[:13],
                    repair.location[:18],
                    status_icon,
                    repair.status,
                    created
                ))
        
        input("\nPress Enter to continue...")

    def manage_repair(self, technician):
        self.clear_screen()
        self.print_header("🔧 MANAGE REPAIR")

        repairs = RepairRequest.objects.filter(technician=technician).order_by('-created_at')
        if not repairs:
            print("\n❌ No assigned repairs")
            input("\nPress Enter to continue...")
            return

        print("\n{:<6} {:<15} {:<20} {:<12} {:<18}".format(
            "ID", "RESIDENT", "LOCATION", "STATUS", "CREATED"
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

            print("{:<6} {:<15} {:<20} {:<2} {:<10} {:<18}".format(
                repair.id,
                repair.resident.user.username[:13],
                repair.location[:18],
                status_icon,
                repair.status,
                created
            ))
        
        try:
            repair_id = int(input("\nEnter Repair ID: "))
            repair = RepairRequest.objects.get(id=repair_id, technician=technician)
            
            # Show repair details
            self.show_repair_details(repair)
            
            # Show status transition options
            menu = """
[1] Change Status to:
    a) PENDING
    b) ON_PROCESS
    c) COMPLETED
    d) CANCELLED
[2] View Work Logs
[0] Back
"""
            print(menu)
            
            choice = input("Select: ").strip()
            
            if choice == '1':
                status_choice = input("Select status (a-d): ").lower()
                status_map = {'a': 'PENDING', 'b': 'ON_PROCESS', 'c': 'COMPLETED', 'd': 'CANCELLED'}
                new_status = status_map.get(status_choice)
                
                if new_status:
                    repair.status = new_status
                    repair.save()
                    print(f"\n✅ Status updated to {new_status}")
            
            elif choice == '2':
                self.view_work_logs(repair)
            
        except ValueError:
            print("\n❌ Invalid input")
        except RepairRequest.DoesNotExist:
            print("\n❌ Repair not found or not assigned to you")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def show_repair_details(self, repair):
        """Display repair details in formatted way"""
        self.clear_screen()
        self.print_header(f"🔧 REPAIR #{repair.id} DETAILS")
        
        print(f"""
👤 Resident      : {repair.resident.user.username} ({repair.resident.room_number})
📍 Location      : {repair.location}
📝 Description   : {repair.description}
🏷️  Type         : {repair.request_type}
📊 Status        : {repair.status}
📅 Created       : {repair.created_at.strftime('%Y-%m-%d %H:%M:%S')}
""")
        
        # Show work logs if any
        logs = repair.logs.all()
        if logs:
            print(f"📋 Work Logs ({logs.count()}):")
            print("-" * 65)
            for log in logs:
                print(f"  {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  → {log.description}")
                print()

    def view_work_logs(self, repair):
        self.clear_screen()
        self.print_header(f"📋 WORK LOGS - Repair #{repair.id}")
        
        logs = repair.logs.all()
        
        if not logs:
            print("\n❌ No work logs yet")
        else:
            print(f"\n📋 Total Logs: {logs.count()}")
            print("-" * 70)
            
            for idx, log in enumerate(logs, 1):
                print(f"\n[{idx}] {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    {log.description}")
        
        input("\nPress Enter to continue...")

    def add_worklog(self, technician):
        self.clear_screen()
        self.print_header("✏️  ADD WORK LOG")
        
        try:
            repair_id = int(input("\nEnter Repair ID: "))
            repair = RepairRequest.objects.get(id=repair_id, technician=technician)
            
            self.show_repair_details(repair)
            
            worklog_desc = input("\nEnter Work Log Description: ")
            
            if not worklog_desc:
                print("\n❌ Description is required")
                input("Press Enter to continue...")
                return
            
            log = WorkLog.objects.create(
                repair_request=repair,
                description=worklog_desc
            )
            
            print(f"\n✅ Work log added successfully!")
            print(f"   Log ID: {log.id}")
            print(f"   Time: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except ValueError:
            print("\n❌ Invalid repair ID")
        except RepairRequest.DoesNotExist:
            print("\n❌ Repair not found or not assigned to you")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def view_work_history(self, technician):
        self.clear_screen()
        self.print_header("🧾 WORK HISTORY")

        qs = RepairRequest.objects.filter(
            technician=technician,
            status='COMPLETED'
        ).select_related('resident__user').order_by('-created_at')

        if not qs.exists():
            print("\n❌ No completed repairs found")
            input("\nPress Enter to continue...")
            return

        print("\nFilter by date range:")
        print("[1] Last 30 days (default)")
        print("[2] Last 90 days")
        print("[3] All")
        date_choice = input("Select: ").strip() or '1'

        print("\nFilter by type:")
        print("[1] ALL (default)")
        print("[2] MAINTENANCE")
        print("[3] COMPLAINT")
        type_choice = input("Select: ").strip() or '1'

        print("\nFilter by rating:")
        print("[1] ALL (default)")
        print("[2] 5")
        print("[3] 4")
        print("[4] 3")
        print("[5] 2")
        print("[6] 1")
        rating_choice = input("Select: ").strip() or '1'

        if date_choice in {'1', '2'}:
            days = 30 if date_choice == '1' else 90
            since = timezone.now() - timedelta(days=days)
            qs = qs.filter(created_at__gte=since)

        if type_choice == '2':
            qs = qs.filter(request_type='MAINTENANCE')
        elif type_choice == '3':
            qs = qs.filter(request_type='COMPLAINT')

        rating_map = {
            '2': 5,
            '3': 4,
            '4': 3,
            '5': 2,
            '6': 1,
        }
        if rating_choice in rating_map:
            qs = qs.filter(rating=rating_map[rating_choice])

        total_completed = RepairRequest.objects.filter(
            technician=technician,
            status='COMPLETED'
        ).count()

        rated_qs = RepairRequest.objects.filter(
            technician=technician,
            status='COMPLETED',
            rating__isnull=False
        )
        avg_rating = rated_qs.aggregate(avg=models.Avg('rating'))['avg'] or 0.0

        now = timezone.localtime(timezone.now())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_count = RepairRequest.objects.filter(
            technician=technician,
            status='COMPLETED',
            created_at__gte=month_start
        ).count()

        print("\n📊 Summary")
        print(f"- Total completed: {total_completed}")
        print(f"- Completed this month: {this_month_count}")
        print(f"- Average rating: {avg_rating:.2f}/5")

        if not qs.exists():
            print("\n❌ No results for selected filters")
            input("\nPress Enter to continue...")
            return

        print("\n{:<6} {:<12} {:<20} {:<8} {:<18}".format(
            "ID", "TYPE", "LOCATION", "RATING", "COMPLETED"
        ))
        print("-" * 70)

        for repair in qs:
            rating_text = f"{repair.rating}/5" if repair.rating else "-"
            created = repair.created_at.strftime("%Y-%m-%d %H:%M")
            print("{:<6} {:<12} {:<20} {:<8} {:<18}".format(
                repair.id,
                repair.request_type,
                repair.location[:18],
                rating_text,
                created
            ))

        input("\nPress Enter to continue...")

    def set_rating(self, repair):
        self.clear_screen()
        self.print_header(f"⭐ RATE REPAIR #{repair.id}")
        
        try:
            print("\n⭐⭐⭐⭐⭐ 5 stars - Excellent")
            print("⭐⭐⭐⭐  4 stars - Good")
            print("⭐⭐⭐    3 stars - Average")
            print("⭐⭐      2 stars - Fair")
            print("⭐        1 star  - Poor")
            
            rating = int(input("\nEnter Rating (1-5): "))
            
            if rating < 1 or rating > 5:
                print("\n❌ Rating must be between 1 and 5")
                input("Press Enter to continue...")
                return
            
            repair.rating = rating
            repair.save()
            
            stars = "⭐" * rating
            print(f"\n✅ Rating set successfully!")
            print(f"   {stars} ({rating}/5)")
            
        except ValueError:
            print("\n❌ Invalid input")
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
        
        input("\nPress Enter to continue...")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title):
        print("╔════════════════════════════════════════════════════════════════╗")
        print(f"║ {title:<62} ║")
        print("╚════════════════════════════════════════════════════════════════╝")
