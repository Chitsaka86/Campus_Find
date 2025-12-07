from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class House(models.Model):
    landlord = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    # Add this
    CATEGORY_CHOICES = [
        ('house', 'House'),
        ('hostel', 'Hostel'),
        ('apartment', 'Apartment'),
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    def __str__(self):
        return self.title

class HouseImage(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='houses/')

    def __str__(self):
        return f"Image for {self.house.title}"
# Create your models here.