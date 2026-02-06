from django.urls import path
from . import views

urlpatterns = [
    path('', views.announcement_list_view, name='announcement_list'),
    path('create/', views.create_announcement_view, name='create_announcement'),
]
