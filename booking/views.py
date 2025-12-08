from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from houses.models import House
from movers.models import MoverService
from .models import Booking, MoverBooking

@login_required(login_url='register')
def property_detail(request, pk):
    """Display property details and booking form"""
    property = get_object_or_404(House, pk=pk)
    
    # Check if tenant has already booked this property
    existing_booking = Booking.objects.filter(tenant=request.user, property=property).first()
    
    context = {
        'property': property,
        'existing_booking': existing_booking,
    }
    return render(request, 'houses/property_detail.html', context)

@login_required(login_url='register')
def create_booking(request, property_id):
    """Create a booking for a property"""
    property = get_object_or_404(House, pk=property_id)
    
    # Check if already booked
    if Booking.objects.filter(tenant=request.user, property=property).exists():
        messages.warning(request, 'You have already booked this property!')
        return redirect('property_detail', pk=property.pk)
    
    if request.method == 'POST':
        try:
            booking = Booking.objects.create(
                tenant=request.user,
                property=property,
                move_in_date=request.POST.get('move_in_date'),
                lease_duration_months=request.POST.get('lease_duration_months', 12),
                tenant_name=request.POST.get('tenant_name'),
                tenant_phone=request.POST.get('tenant_phone'),
                tenant_email=request.POST.get('tenant_email'),
                message=request.POST.get('message', ''),
            )
            
            # Check if mover booking is requested
            mover_id = request.POST.get('mover_id')
            if mover_id:
                mover = get_object_or_404(MoverService, pk=mover_id)
                pickup_location = request.POST.get('pickup_location', '').strip()
                dropoff_location = request.POST.get('dropoff_location', '').strip()
                distance_km = float(request.POST.get('distance_km', 0))
                
                if pickup_location and dropoff_location and distance_km > 0:
                    # Get mover's current rating
                    rating = mover.rating_summary.get('average', 0)
                    
                    MoverBooking.objects.create(
                        booking=booking,
                        mover=mover,
                        pickup_location=pickup_location,
                        dropoff_location=dropoff_location,
                        distance_km=distance_km,
                        base_rate=mover.base_rate,
                        rate_per_km=50,  # Default rate per km
                        mover_rating=rating,
                    )
            
            messages.success(request, 'Booking request sent! The landlord will review it soon.')
            return redirect('my_bookings')
        except Exception as e:
            messages.error(request, f'Error creating booking: {str(e)}')
            return redirect('property_detail', pk=property.pk)
    
    # Get available movers
    movers = MoverService.objects.annotate(
        avg_rating=Avg('ratings__score')
    ).order_by('-avg_rating')
    
    context = {
        'property': property,
        'movers': movers
    }
    return render(request, 'booking/create_booking.html', context)

@login_required(login_url='register')
def my_bookings(request):
    """View tenant's bookings"""
    bookings = Booking.objects.filter(tenant=request.user).select_related('property')
    
    context = {
        'bookings': bookings,
        'pending': bookings.filter(status='pending').count(),
        'approved': bookings.filter(status='approved').count(),
        'rejected': bookings.filter(status='rejected').count(),
    }
    return render(request, 'booking/my_bookings.html', context)

@login_required(login_url='register')
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, pk=booking_id, tenant=request.user)
    
    if request.method == 'POST':
        if booking.status == 'pending':
            booking.status = 'cancelled'
            booking.save()
            messages.success(request, 'Booking cancelled successfully!')
        elif booking.status == 'approved':
            # If approved booking is cancelled, increase available units
            booking.status = 'cancelled'
            booking.save()
            
            if booking.property.available_units < booking.property.total_units:
                booking.property.available_units += 1
                booking.property.save()  # This will auto-update is_available via save method
                messages.success(request, f'Booking cancelled! Property now has {booking.property.available_units} unit(s) available.')
            else:
                messages.success(request, 'Booking cancelled!')
        else:
            messages.error(request, 'You can only cancel pending or approved bookings!')
        return redirect('my_bookings')
    
    return render(request, 'booking/cancel_booking.html', {'booking': booking})

@login_required(login_url='register')
@login_required(login_url='register')
def book_mover(request, mover_id):
    """Book a mover service directly"""
    mover = get_object_or_404(MoverService, pk=mover_id)
    
    if request.method == 'POST':
        try:
            tenant_name = request.POST.get('tenant_name', '').strip()
            tenant_phone = request.POST.get('tenant_phone', '').strip()
            tenant_email = request.POST.get('tenant_email', '').strip()
            pickup_location = request.POST.get('pickup_location', '').strip()
            dropoff_location = request.POST.get('dropoff_location', '').strip()
            distance_km = float(request.POST.get('distance_km', 0))
            
            if not all([tenant_name, tenant_phone, tenant_email, pickup_location, dropoff_location, distance_km > 0]):
                messages.error(request, 'Please fill in all required fields.')
                return redirect('book_mover', mover_id=mover_id)
            
            # Get mover's current rating
            rating = mover.rating_summary.get('average', 0)
            
            # Calculate total cost
            base_rate = float(mover.base_rate)
            rate_per_km = 50
            total_cost = base_rate + (distance_km * rate_per_km)
            distance_charge = distance_km * rate_per_km
            
            # Store serializable data in session for confirmation
            request.session['pending_mover_booking'] = {
                'mover_id': mover_id,
                'mover_name': mover.name,
                'mover_location': mover.location,
                'mover_phone': mover.phone,
                'tenant_name': tenant_name,
                'tenant_phone': tenant_phone,
                'tenant_email': tenant_email,
                'pickup_location': pickup_location,
                'dropoff_location': dropoff_location,
                'distance_km': float(distance_km),
                'base_rate': float(base_rate),
                'rate_per_km': float(rate_per_km),
                'distance_charge': float(distance_charge),
                'total_cost': float(total_cost),
                'mover_rating': float(rating),
            }
            
            return redirect('confirm_mover_booking')
        except Exception as e:
            messages.error(request, f'Error booking mover: {str(e)}')
            return redirect('book_mover', mover_id=mover_id)
    
    context = {'mover': mover}
    return render(request, 'booking/book_mover.html', context)


@login_required(login_url='register')
def confirm_mover_booking(request):
    """Confirm mover booking"""
    mover_booking_data = request.session.get('pending_mover_booking')
    
    if not mover_booking_data:
        messages.error(request, 'No pending mover booking found.')
        return redirect('movers_list')
    
    if request.method == 'POST':
        try:
            # Get mover
            mover = MoverService.objects.get(pk=mover_booking_data['mover_id'])
            
            # Create mover booking record
            mover_booking = MoverBooking.objects.create(
                mover=mover,
                tenant=request.user,
                tenant_name=mover_booking_data['tenant_name'],
                tenant_phone=mover_booking_data['tenant_phone'],
                tenant_email=mover_booking_data['tenant_email'],
                pickup_location=mover_booking_data['pickup_location'],
                dropoff_location=mover_booking_data['dropoff_location'],
                distance_km=mover_booking_data['distance_km'],
                base_rate=mover_booking_data['base_rate'],
                rate_per_km=mover_booking_data['rate_per_km'],
                mover_rating=mover_booking_data['mover_rating'],
                status='pending',
            )
            
            messages.success(request, f'Booking confirmed! {mover.name} will review and contact you.')
            
            # Clear session
            del request.session['pending_mover_booking']
            
            # Redirect to tenant's mover bookings
            return redirect('my_mover_bookings')
        except Exception as e:
            messages.error(request, f'Error confirming booking: {str(e)}')
            return redirect('confirm_mover_booking')
    
    context = {'mover_booking': mover_booking_data}
    return render(request, 'booking/confirm_mover_booking.html', context)


# Landlord views
@login_required(login_url='register')
def manage_bookings(request):
    """Landlord view bookings for their properties"""
    # Get all bookings for properties owned by this landlord
    bookings = Booking.objects.filter(property__landlord=request.user).select_related('property', 'tenant')
    
    context = {
        'bookings': bookings,
        'pending': bookings.filter(status='pending').count(),
        'approved': bookings.filter(status='approved').count(),
        'rejected': bookings.filter(status='rejected').count(),
    }
    return render(request, 'booking/manage_bookings.html', context)

@login_required(login_url='register')
def approve_booking(request, booking_id):
    """Approve a booking"""
    booking = get_object_or_404(Booking, pk=booking_id, property__landlord=request.user)
    
    if request.method == 'POST':
        booking.status = 'approved'
        booking.save()
        
        # Decrease available units when booking is approved
        if booking.property.available_units > 0:
            booking.property.available_units -= 1
            booking.property.save()  # This will auto-update is_available via save method
            
            if booking.property.available_units == 0:
                messages.success(request, 'Booking approved! All units are now booked.')
            else:
                messages.success(request, f'Booking approved! {booking.property.available_units} unit(s) remaining.')
        else:
            messages.warning(request, 'Booking approved but no units were available to decrease.')
        
        return redirect('manage_bookings')


# Mover Booking views for tenants
@login_required(login_url='register')
def my_mover_bookings(request):
    """View tenant's mover bookings"""
    mover_bookings = MoverBooking.objects.filter(tenant=request.user).select_related('mover').order_by('-created_at')
    
    context = {
        'mover_bookings': mover_bookings,
        'pending': mover_bookings.filter(status='pending').count(),
        'confirmed': mover_bookings.filter(status='confirmed').count(),
        'rejected': mover_bookings.filter(status='rejected').count(),
    }
    return render(request, 'booking/my_mover_bookings.html', context)


@login_required(login_url='register')
def cancel_mover_booking(request, booking_id):
    """Cancel a mover booking"""
    mover_booking = get_object_or_404(MoverBooking, pk=booking_id, tenant=request.user)
    
    if request.method == 'POST':
        if mover_booking.status in ['pending', 'confirmed']:
            mover_booking.status = 'cancelled'
            mover_booking.save()
            messages.success(request, 'Mover booking cancelled successfully!')
        else:
            messages.error(request, 'You can only cancel pending or confirmed bookings!')
        return redirect('my_mover_bookings')
    
    return render(request, 'booking/cancel_mover_booking.html', {'mover_booking': mover_booking})


# Mover views for managing bookings
@login_required(login_url='register')
def mover_manage_bookings(request):
    """Mover view bookings for their services"""
    mover_bookings = (
        MoverBooking.objects
        .filter(mover__owner=request.user)
        .select_related('mover', 'tenant')
        .order_by('-created_at')
    )

    context = {
        'mover_bookings': mover_bookings,
        'pending': mover_bookings.filter(status='pending').count(),
        'confirmed': mover_bookings.filter(status='confirmed').count(),
        'rejected': mover_bookings.filter(status='rejected').count(),
    }
    return render(request, 'booking/mover_manage_bookings.html', context)


@login_required(login_url='register')
def approve_mover_booking(request, booking_id):
    """Mover approves a booking"""
    mover_booking = get_object_or_404(MoverBooking, pk=booking_id, mover__owner=request.user)
    
    if request.method == 'POST':
        if mover_booking.status == 'pending':
            mover_booking.status = 'confirmed'
            mover_booking.save()
            messages.success(request, f'Booking approved! Tenant will be notified.')
        else:
            messages.error(request, 'Only pending bookings can be approved.')
        return redirect('mover_manage_bookings')
    
    return render(request, 'booking/approve_mover_booking.html', {'mover_booking': mover_booking})


@login_required(login_url='register')
def reject_mover_booking(request, booking_id):
    """Mover rejects a booking"""
    mover_booking = get_object_or_404(MoverBooking, pk=booking_id, mover__owner=request.user)
    
    if request.method == 'POST':
        if mover_booking.status == 'pending':
            mover_booking.status = 'rejected'
            mover_booking.save()
            messages.success(request, 'Booking rejected!')
        else:
            messages.error(request, 'Only pending bookings can be rejected.')
        return redirect('mover_manage_bookings')
    
    return render(request, 'booking/reject_mover_booking.html', {'mover_booking': mover_booking})

    return render(request, 'booking/booking_detail.html', {'booking': booking, 'action': 'approve'})

@login_required(login_url='register')
def reject_booking(request, booking_id):
    """Reject a booking"""
    booking = get_object_or_404(Booking, pk=booking_id, property__landlord=request.user)
    
    if request.method == 'POST':
        booking.status = 'rejected'
        booking.save()
        messages.success(request, 'Booking rejected!')
        return redirect('manage_bookings')
    
    return render(request, 'booking/booking_detail.html', {'booking': booking, 'action': 'reject'})

