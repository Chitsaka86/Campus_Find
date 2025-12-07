from django.urls import path
from . import views

urlpatterns = [
    # Tenant URLs
    path('create/<int:property_id>/', views.create_booking, name='create_booking'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    
    # Landlord URLs
    path('manage/', views.manage_bookings, name='manage_bookings'),
    path('approve/<int:booking_id>/', views.approve_booking, name='approve_booking'),
    path('reject/<int:booking_id>/', views.reject_booking, name='reject_booking'),
]
