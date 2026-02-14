from django.urls import path
from . import views

urlpatterns = [
    path('', views.repair_list_view, name='repair_list'),
    path('new/', views.create_repair_view, name='create_repair'),
    path('history/', views.technician_work_history_view, name='technician_work_history'),
    path('<int:pk>/', views.repair_detail_view, name='repair_detail'),
    path('<int:pk>/assign/', views.assign_technician_view, name='assign_technician'),
    path('<int:pk>/update-status/', views.update_repair_status_view, name='update_repair_status'),
    path('<int:pk>/rate/', views.rate_repair_view, name='rate_repair'),
    

]
