from django.urls import path
from . import views

urlpatterns = [
    path('', views.lost_found_list_view, name='lost_found_list'),
    path('report/', views.report_item_view, name='report_item'),
    path('claim/<int:pk>/', views.claim_item_view, name='claim_item'),
    path('resolve/<int:pk>/', views.resolve_item_view, name='resolve_item'),
    path('approve/<int:pk>/', views.approve_item_view, name='approve_item'),
]
