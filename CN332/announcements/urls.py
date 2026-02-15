from django.urls import path
from . import views

urlpatterns = [
    path('', views.announcement_list_view, name='announcement_list'),
    path('create/', views.create_announcement_view, name='create_announcement'),
    path('detail/<int:pk>/', views.announcement_detail_view, name='announcement_detail'),
    path('edit/<int:pk>/', views.edit_announcement_view, name='edit_announcement'),
    path('attachment/delete/<int:pk>/', views.delete_attachment_view, name='delete_attachment'),
]
