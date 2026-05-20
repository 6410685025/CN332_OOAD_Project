from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import authenticate
from users.models import User, Staff, Technician
from repairs.models import RepairRequest
import os
import getpass


class Command(BaseCommand):
    help = 'Interactive CLI dashboard for Juristic/Manager role'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the juristic officer/manager')

    def handle(self, *args, **options):
        user = self.login_screen()
        if not user:
            raise CommandError("Authentication failed")
        
        try:
            staff = user.staff
        except Staff.DoesNotExist:
            raise CommandError(f"User {user.username} is not a staff member")

        self.run_dashboard(staff, user)



    def run_dashboard(self, staff, user):
        """Main dashboard loop"""
        while True:
            self.clear_screen()
            self.print_header(f"Welcome {user.first_name or user.username} (JURISTIC)")
            self.print_dashboard_menu()
            
            choice = input("\nSelect: ").strip()
            
            if choice == '1':
                self.view_pending_requests()
            elif choice == '2':
                self.confirm_request()
            elif choice == '0':
                self.stdout.write(self.style.SUCCESS("Goodbye!"))
                break
            else:
                input("\n❌ Invalid choice. Press Enter to continue...")

    def login_screen(self):
        attempts = 3
        while attempts > 0:
            self.clear_screen()
            self.print_header("JURISTIC CLI - LOGIN")
            username = input("\nUsername: ").strip()
            password = getpass.getpass("Password: ")

            user = authenticate(username=username, password=password)
            if user:
                return user

            attempts -= 1
            print("\n❌ Login failed - Invalid username or password")
            if attempts > 0:
                print(f"Attempts left: {attempts}")
                input("Press Enter to try again...")
        return None

    def print_dashboard_menu(self):
        pending_count = RepairRequest.objects.filter(status='PENDING').count()
        in_process_count = RepairRequest.objects.filter(status='ON_PROCESS').count()
        
        menu = f"""
╔═══════════════════════════════════════════════════════════════╗
║                  JURISTIC DASHBOARD                           ║
╚═══════════════════════════════════════════════════════════════╝

📊 Outstanding Repairs: PENDING ({pending_count}) | IN PROCESS ({in_process_count})

[1] View Pending Requests
[2] Confirm Request
[0] Logout
"""
        print(menu)

    def view_pending_requests(self):
        self.clear_screen()
        self.print_header("=== PENDING REQUESTS ===")
        
        repairs = RepairRequest.objects.filter(status='PENDING').order_by('-created_at')
        
        if not repairs:
            print("\n! No records found.")
        else:
            for idx, repair in enumerate(repairs, 1):
                print(f"\n[{idx}] {repair.request_type} Job")
                print(f"Job ID        : {repair.id}")
                print(f"Category      : {repair.request_type}")
                print(f"Description   : {repair.description}")
                print(f"Resident      : {repair.resident.user.first_name} {repair.resident.user.last_name}")
                print(f"Status        : Waiting for confirmation")
                print(f"Assigned To   : -")
                print("-" * 65)
        
        input("Press Enter to continue...")

    def confirm_request(self):
        self.clear_screen()
        self.print_header("=== PENDING REQUESTS ===")
        
        repairs = RepairRequest.objects.filter(status='PENDING').order_by('-created_at')
        
        if not repairs:
            print("\n! No pending requests to confirm.")
            input("Press Enter to continue...")
            return
        
        for idx, repair in enumerate(repairs, 1):
            print(f"\n[{idx}] {repair.request_type} Job")
            print(f"Job ID        : {repair.id}")
            print(f"Category      : {repair.request_type}")
            print(f"Description   : {repair.description}")
            print(f"Resident      : {repair.resident.user.first_name} {repair.resident.user.last_name}")
            print(f"Status        : Waiting for confirmation")
            print(f"Assigned To   : -")
            print("-" * 65)
        
        while True:
            try:
                repair_id = input("\nEnter Job ID to confirm: ").strip()
                
                if not repair_id:
                    break
                
                repair = RepairRequest.objects.get(id=int(repair_id), status='PENDING')
                
                # Show available technicians
                technicians = Technician.objects.all()
                
                if not technicians:
                    print("\n❌ No technicians available")
                    input("Press Enter to continue...")
                    return
                
                print("\n👨‍🔧 SELECT TECHNICIAN:")
                print("-" * 50)
                tech_list = []
                for idx, tech in enumerate(technicians, 1):
                    status_icon = '✅' if tech.availability == 'AVAILABLE' else '🔴'
                    print(f"[{idx}] {tech.user.first_name} {tech.user.last_name} {status_icon}")
                    tech_list.append(tech)
                
                tech_choice = int(input("\nSelect Technician (number): "))
                technician = tech_list[tech_choice - 1]
                
                # Assign to technician
                repair.technician = technician
                repair.status = 'ON_PROCESS'
                repair.save()
                
                print(f"\n✅ System assigned job #{repair_id} to {technician.user.first_name} {technician.user.last_name}")
                
                # Show next pending request or exit
                remaining = RepairRequest.objects.filter(status='PENDING').count()
                if remaining == 0:
                    print("\n✅ All pending requests have been assigned!")
                    break
                
                input("Press Enter to continue...")
                self.clear_screen()
                print("\n=== PENDING REQUESTS ===\n")
                
                repairs = RepairRequest.objects.filter(status='PENDING').order_by('-created_at')
                for idx, repair in enumerate(repairs, 1):
                    print(f"[{idx}] {repair.request_type} Job")
                    print(f"Job ID        : {repair.id}")
                    print(f"Category      : {repair.request_type}")
                    print(f"Description   : {repair.description}")
                    print(f"Resident      : {repair.resident.user.first_name} {repair.resident.user.last_name}")
                    print(f"Status        : Waiting for confirmation")
                    print(f"Assigned To   : -")
                    print("-" * 65)
                
            except ValueError:
                print("\n❌ Invalid input")
            except (RepairRequest.DoesNotExist, IndexError):
                print("\n❌ Job or technician not found")
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self, title):
        print("╔════════════════════════════════════════════════════════════════╗")
        print(f"║ {title:<62} ║")
        print("╚════════════════════════════════════════════════════════════════╝")
