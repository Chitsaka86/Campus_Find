from django.urls import path
from . import views

urlpatterns = [
    path('', views.movers_list, name='movers_list'),
    path('add/', views.add_mover, name='add_mover'),
    path('my-services/', views.my_mover_services, name='my_mover_services'),
    path('edit/<int:pk>/', views.edit_mover, name='edit_mover'),
    path('manage-bookings/', views.manage_mover_bookings, name='manage_mover_bookings'),
    path('<int:pk>/', views.mover_detail, name='mover_detail'),
]
