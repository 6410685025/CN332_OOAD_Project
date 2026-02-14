from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('resident/', views.resident_dashboard, name='resident_dashboard'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('technician/', views.technician_dashboard, name='technician_dashboard'),
    path('residents/', views.residents_list_view, name='residents_list'),
    path('residents/create/', views.create_resident_view, name='create_resident'),
    path('residents/<int:resident_id>/get/', views.get_resident_view, name='get_resident'),
    path('residents/<int:resident_id>/update/', views.update_resident_view, name='update_resident'),
    path('residents/<int:resident_id>/delete/', views.delete_resident_view, name='delete_resident'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/update-profile/', views.update_profile_view, name='update_profile'),
    path('settings/change-password/', views.change_password_view, name='change_password'),
    path('settings/social-disconnect/', views.social_disconnect_view, name='social_disconnect'),
]
