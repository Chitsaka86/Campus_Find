from django.urls import path
from . import views

urlpatterns = [
    # Tenant Property Booking URLs
    path('create/<int:property_id>/', views.create_booking, name='create_booking'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    
    # Tenant Mover Booking URLs
    path('mover/confirm/', views.confirm_mover_booking, name='confirm_mover_booking'),
    path('mover/<int:mover_id>/', views.book_mover, name='book_mover'),
    path('my-mover-bookings/', views.my_mover_bookings, name='my_mover_bookings'),
    path('mover-booking/cancel/<int:booking_id>/', views.cancel_mover_booking, name='cancel_mover_booking'),
    
    # Mover Booking Management URLs
    path('mover-manage/', views.mover_manage_bookings, name='mover_manage_bookings'),
    path('mover-booking/approve/<int:booking_id>/', views.approve_mover_booking, name='approve_mover_booking'),
    path('mover-booking/reject/<int:booking_id>/', views.reject_mover_booking, name='reject_mover_booking'),
    
    # Landlord Property Booking URLs
    path('manage/', views.manage_bookings, name='manage_bookings'),
    path('approve/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    path('reject/<int:booking_id>/', views.reject_booking, name='reject_booking'),
]
