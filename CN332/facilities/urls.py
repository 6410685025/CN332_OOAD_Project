from django.urls import path
from . import views

urlpatterns = [
    path('', views.facility_list_view, name='facility_list'),
    path('book/', views.create_booking_view, name='create_booking'),
    path('my-bookings/', views.my_bookings_view, name='my_bookings'),
    path('all-bookings/', views.all_bookings_view, name='all_bookings'),
    path('confirm/<int:pk>/', views.confirm_booking_view, name='confirm_booking'),
    path('cancel/<int:pk>/', views.cancel_booking_view, name='cancel_booking'),
    path('toggle/<int:pk>/', views.toggle_facility_view, name='toggle_facility'),
    path('create/', views.create_facility_view, name='create_facility'),
]
