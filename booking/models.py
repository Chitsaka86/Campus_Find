from django.db import models
from django.contrib.auth import get_user_model
from houses.models import House

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

