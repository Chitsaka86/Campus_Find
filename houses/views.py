from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import House, HouseImage

def home(request):
    stats = {
        'houses': House.objects.filter(category='standalone').count(),
        'hostels': House.objects.filter(category='hostel').count(),
        'apartments': House.objects.filter(category='apartment').count(),
        'roommates': House.objects.filter(category='roommate').count(),
    }
    recent_listings = House.objects.filter(is_available=True).order_by('-created_at')[:10]
    context = {
        'stats': stats,
        'recent_listings': recent_listings
    }
    return render(request, 'home.html', context)

def property_detail(request, pk):
    """Display property details"""
    property = get_object_or_404(House, pk=pk)
    context = {'property': property}
    return render(request, 'houses/property_detail.html', context)

@login_required(login_url='register')
def add_property(request):
    if request.method == 'POST':
        try:
            total_units = int(request.POST.get('total_units', 1))
            # Create the house
            house = House.objects.create(
                landlord=request.user,
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                category=request.POST.get('category'),
                price=request.POST.get('price'),
                number_of_rooms=request.POST.get('number_of_rooms', 1),
                total_units=total_units,
                available_units=total_units,  # Initially all units are available
                location=request.POST.get('location'),
                latitude=request.POST.get('latitude') or None,
                longitude=request.POST.get('longitude') or None,
                amenities=','.join(request.POST.getlist('amenities')),
                contact_phone=request.POST.get('contact_phone'),
                contact_email=request.POST.get('contact_email', ''),
            )
            
            # Handle multiple image uploads
            images = request.FILES.getlist('images')
            for index, image in enumerate(images):
                HouseImage.objects.create(
                    house=house,
                    image=image,
                    is_primary=(index == 0)  # First image is primary
                )
            
            messages.success(request, 'Property added successfully!')
            return redirect('my_properties')
        except Exception as e:
            messages.error(request, f'Error adding property: {str(e)}')
            return redirect('add_property')
    
    context = {
        'categories': House.CATEGORY_CHOICES,
        'amenities': House.AMENITIES_CHOICES,
    }
    return render(request, 'houses/add_property.html', context)

@login_required(login_url='register')
def my_properties(request):
    properties = House.objects.filter(landlord=request.user)
    context = {'properties': properties}
    return render(request, 'houses/my_properties.html', context)

@login_required(login_url='register')
def edit_property(request, pk):
    house = get_object_or_404(House, pk=pk, landlord=request.user)
    
    if request.method == 'POST':
        try:
            house.title = request.POST.get('title')
            house.description = request.POST.get('description')
            house.category = request.POST.get('category')
            house.price = request.POST.get('price')
            house.number_of_rooms = request.POST.get('number_of_rooms', 1)
            
            # Update total units and adjust available units proportionally
            new_total_units = int(request.POST.get('total_units', 1))
            if new_total_units != house.total_units:
                # Calculate the difference
                diff = new_total_units - house.total_units
                house.total_units = new_total_units
                house.available_units = max(0, house.available_units + diff)
            
            house.location = request.POST.get('location')
            house.latitude = request.POST.get('latitude') or None
            house.longitude = request.POST.get('longitude') or None
            house.amenities = ','.join(request.POST.getlist('amenities'))
            house.contact_phone = request.POST.get('contact_phone')
            house.contact_email = request.POST.get('contact_email', '')
            house.save()
            
            # Handle new images
            images = request.FILES.getlist('images')
            for image in images:
                HouseImage.objects.create(house=house, image=image)
            
            messages.success(request, 'Property updated successfully!')
            return redirect('my_properties')
        except Exception as e:
            messages.error(request, f'Error updating property: {str(e)}')
    
    context = {
        'house': house,
        'categories': House.CATEGORY_CHOICES,
        'amenities': House.AMENITIES_CHOICES,
        'selected_amenities': house.get_amenities_list(),
    }
    return render(request, 'houses/edit_property.html', context)

@login_required(login_url='register')
def delete_property(request, pk):
    house = get_object_or_404(House, pk=pk, landlord=request.user)
    if request.method == 'POST':
        house.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('my_properties')
    return render(request, 'houses/delete_confirm.html', {'house': house})
