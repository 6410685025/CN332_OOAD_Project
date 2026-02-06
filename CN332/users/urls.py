from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('resident/', views.resident_dashboard, name='resident_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('technician/', views.technician_dashboard, name='technician_dashboard'),
    path('residents/', views.residents_list_view, name='residents_list'),
    path('settings/', views.settings_view, name='settings'),
]
