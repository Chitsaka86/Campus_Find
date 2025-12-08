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

def browse_properties(request):
    """Browse all available properties with filters"""
    properties = House.objects.filter(is_available=True).order_by('-created_at')
    
    # Get filter parameters
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    location = request.GET.get('location')
    rooms = request.GET.get('rooms')
    
    # Apply filters
    if category:
        properties = properties.filter(category=category)
    if min_price:
        properties = properties.filter(price__gte=min_price)
    if max_price:
        properties = properties.filter(price__lte=max_price)
    if location:
        properties = properties.filter(location__icontains=location)
    if rooms:
        properties = properties.filter(number_of_rooms=rooms)
    
    # Get categories for filter dropdown
    categories = House.CATEGORY_CHOICES
    
    context = {
        'properties': properties,
        'categories': categories,
        'selected_category': category,
        'selected_location': location,
        'selected_rooms': rooms,
        'min_price': min_price,
        'max_price': max_price,
        'total_count': properties.count(),
    }
    return render(request, 'houses/browse_properties.html', context)

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

            # Handle up to 3 separate image fields
            image_fields = ['image1', 'image2', 'image3']
            for index, field in enumerate(image_fields):
                image = request.FILES.get(field)
                if image:
                    HouseImage.objects.create(
                        house=house,
                        image=image,
                        is_primary=(index == 0)
                    )
                print(f"Created image {index + 1}: {image.name}")
            
            print(f"DEBUG: Total images saved: {house.images.count()}")
            
            messages.success(request, f'Property added successfully!')
            return redirect('my_properties')
        except Exception as e:
            import traceback
            print(f"ERROR: {str(e)}")
            traceback.print_exc()
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
            # Basic fields (fallback to existing values if missing)
            house.title = request.POST.get('title') or house.title
            house.description = request.POST.get('description') or house.description
            house.category = request.POST.get('category') or house.category
            price_val = request.POST.get('price')
            house.price = price_val if price_val not in [None, ''] else house.price
            house.number_of_rooms = request.POST.get('number_of_rooms', house.number_of_rooms)
            
            # Update total units and adjust available units proportionally
            new_total_units_raw = request.POST.get('total_units')
            new_total_units = int(new_total_units_raw) if new_total_units_raw not in [None, ''] else house.total_units
            if new_total_units != house.total_units:
                # Calculate the difference
                diff = new_total_units - house.total_units
                house.total_units = new_total_units
                house.available_units = max(0, house.available_units + diff)
            
            house.location = request.POST.get('location') or house.location
            lat_val = request.POST.get('latitude', '').strip()
            house.latitude = float(lat_val) if lat_val and lat_val != 'None' else house.latitude
            lon_val = request.POST.get('longitude', '').strip()
            house.longitude = float(lon_val) if lon_val and lon_val != 'None' else house.longitude
            house.amenities = ','.join(request.POST.getlist('amenities'))
            house.contact_phone = request.POST.get('contact_phone') or house.contact_phone
            house.contact_email = request.POST.get('contact_email', house.contact_email)
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

@login_required(login_url='register')
def delete_property_image(request, image_id):
    """Delete a property image"""
    image = get_object_or_404(HouseImage, pk=image_id, house__landlord=request.user)
    house_id = image.house.id
    image.delete()
    messages.success(request, 'Image deleted successfully!')
    return redirect('edit_property', pk=house_id)
