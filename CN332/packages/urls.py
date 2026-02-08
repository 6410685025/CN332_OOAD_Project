from django.urls import path
from . import views

urlpatterns = [
    path('', views.package_list_view, name='package_list'),
    path('receive/', views.receive_package_view, name='receive_package'),
    path('pickup/<int:pk>/', views.mark_picked_up_view, name='mark_picked_up'),
    path('receive/<int:pk>/', views.receive_package_resident_view, name='receive_package_resident'),
]
