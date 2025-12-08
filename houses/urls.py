from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.browse_properties, name='browse_properties'),
    path('property/add/', views.add_property, name='add_property'),
    path('property/<int:pk>/', views.property_detail, name='property_detail'),
    path('property/my-properties/', views.my_properties, name='my_properties'),
    path('property/edit/<int:pk>/', views.edit_property, name='edit_property'),
    path('property/delete/<int:pk>/', views.delete_property, name='delete_property'),
    path('property/image/delete/<int:image_id>/', views.delete_property_image, name='delete_property_image'),
]