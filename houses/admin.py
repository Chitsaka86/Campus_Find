from django.contrib import admin
from .models import House, HouseImage

# Inline model for house images
class HouseImageInline(admin.TabularInline):
    model = HouseImage           # This is the model to show inline
    extra = 3                    # Number of extra empty image fields by default
    max_num = 10                 # Optional: maximum number of images per house

# House admin
@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('title', 'landlord', 'price', 'location', 'created_at')
    search_fields = ('title', 'location')
    list_filter = ('location', 'created_at')
    inlines = [HouseImageInline]  # Link the inline to House

# Optional: separate admin for HouseImage (still accessible)
@admin.register(HouseImage)
class HouseImageAdmin(admin.ModelAdmin):
    list_display = ('house', 'image')
