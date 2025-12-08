from django.db import models
from django.contrib.auth import get_user_model
from houses.models import House
from movers.models import MoverService

User = get_user_model()

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Relationships
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    property = models.ForeignKey(House, on_delete=models.CASCADE, related_name='bookings')
    
    # Booking Details
    move_in_date = models.DateField(help_text="Intended move-in date")
    lease_duration_months = models.PositiveIntegerField(default=12, help_text="Duration in months")
    
    # Tenant Info
    tenant_name = models.CharField(max_length=200)
    tenant_phone = models.CharField(max_length=20)
    tenant_email = models.EmailField()
    
    # Message
    message = models.TextField(blank=True, help_text="Tenant's message to landlord")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'property')  # Prevent duplicate bookings
    
    def __str__(self):
        return f"Booking for {self.property.title} by {self.tenant.email}"


class MoverBooking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Relationships
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='mover_booking', null=True, blank=True)
    mover = models.ForeignKey(MoverService, on_delete=models.SET_NULL, null=True, related_name='mover_bookings')
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mover_bookings', null=True, blank=True)
    
    # Location Details
    pickup_location = models.CharField(max_length=300, help_text="Current location (where items are being moved from)")
    dropoff_location = models.CharField(max_length=300, help_text="New location (where items are being moved to)")
    
    # Tenant Contact Info
    tenant_name = models.CharField(max_length=200, blank=True, default='')
    tenant_phone = models.CharField(max_length=50, blank=True, default='')
    tenant_email = models.EmailField(blank=True, default='')
    
    # Distance & Pricing
    distance_km = models.DecimalField(max_digits=8, decimal_places=2, help_text="Distance in kilometers")
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base rate from mover")
    rate_per_km = models.DecimalField(max_digits=10, decimal_places=2, default=50, help_text="Rate per km")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total cost (base_rate + distance_km * rate_per_km)")
    
    # Mover Info
    mover_rating = models.DecimalField(max_digits=3, decimal_places=1, default=0, help_text="Mover's average rating at booking time")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Calculate total cost: base_rate + (distance_km * rate_per_km)
        self.total_cost = self.base_rate + (self.distance_km * self.rate_per_km)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Moving booking by {self.tenant_name} with {self.mover.name if self.mover else 'Unknown'}"
