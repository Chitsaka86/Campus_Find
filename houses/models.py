from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class House(models.Model):
    CATEGORY_CHOICES = [
        ('standalone', 'Stand Alone House'),
        ('hostel', 'Hostel'),
        ('apartment', 'Apartment'),
        ('roommate', 'Roommate'),
    ]
    
    AMENITIES_CHOICES = [
        ('wifi', 'WiFi'),
        ('parking', 'Parking'),
        ('security', '24/7 Security'),
        ('water', 'Water Supply'),
        ('electricity', 'Electricity'),
        ('gym', 'Gym'),
        ('pool', 'Swimming Pool'),
        ('laundry', 'Laundry'),
        ('furnished', 'Furnished'),
        ('ac', 'Air Conditioning'),
        ('heating', 'Heating'),
        ('balcony', 'Balcony'),
    ]
    
    # Basic Info
    landlord = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200, help_text="Property name/title")
    description = models.TextField(help_text="Detailed description of the property")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Pricing & Rooms
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Monthly rent in KSh")
    number_of_rooms = models.PositiveIntegerField(default=1)
    total_units = models.PositiveIntegerField(default=1, help_text="Total number of units/apartments available")
    available_units = models.PositiveIntegerField(default=1, help_text="Currently available units")
    
    # Location
    location = models.CharField(max_length=200, help_text="Address/Area")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Amenities (stored as comma-separated values)
    amenities = models.CharField(max_length=500, blank=True, help_text="Comma-separated amenities")
    
    # Contact Info
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField(blank=True)
    
    # Status & Timestamps
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Property'
        verbose_name_plural = 'Properties'

    def __str__(self):
        return self.title
    
    def get_amenities_list(self):
        """Return amenities as a list"""
        if self.amenities:
            return self.amenities.split(',')
        return []
    
    def save(self, *args, **kwargs):
        """Auto-update is_available based on available_units"""
        if self.available_units > 0:
            self.is_available = True
        else:
            self.is_available = False
        super().save(*args, **kwargs)

class HouseImage(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='houses/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'uploaded_at']

    def __str__(self):
        return f"Image for {self.house.title}"