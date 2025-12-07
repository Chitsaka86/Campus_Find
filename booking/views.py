from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from houses.models import House
from .models import Booking

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
            messages.success(request, 'Booking request sent! The landlord will review it soon.')
            return redirect('my_bookings')
        except Exception as e:
            messages.error(request, f'Error creating booking: {str(e)}')
            return redirect('property_detail', pk=property.pk)
    
    context = {'property': property}
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

