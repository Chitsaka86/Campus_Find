from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                if user.is_active:
                    auth_login(request, user)
                    messages.success(request, f'Welcome back, {user.username}!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Your account is not active. Please verify your email.')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email.')
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')
    
    return render(request, 'accounts/login.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter a valid email address')
            return redirect('register')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            
            # Generate and send magic link again
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            magic_link = f"{request.build_absolute_uri(reverse('verify_email', kwargs={'uidb64': uid, 'token': token}))}"
            
            try:
                send_mail(
                    subject='Your Campus Find Magic Link',
                    message=f'''Hello,

Click the link below to verify your email and access your dashboard:

{magic_link}

This link will expire in 24 hours.

Best regards,
Campus Find Team''',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, 'Magic link sent to your email!')
                return redirect('register')
            except Exception as e:
                messages.error(request, f'Error sending email. Please try again.')
                return redirect('register')
        
        # Create new user with email as username
        try:
            username = email.split('@')[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(username=username, email=email)
            user.is_active = False  # Deactivate until email is verified
            user.save()
        except Exception as e:
            messages.error(request, 'Error creating account. Please try again.')
            return redirect('register')
        
        # Generate magic link token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create magic link
        magic_link = f"{request.build_absolute_uri(reverse('verify_email', kwargs={'uidb64': uid, 'token': token}))}"
        
        # Send email with magic link
        try:
            send_mail(
                subject='Your Campus Find Magic Link',
                message=f'''Hello,

Click the link below to verify your email and access your dashboard:

{magic_link}

This link will expire in 1 hour.

If you didn't request this, please ignore this email.

Best regards,
Campus Find Team''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, 'Check your email for a magic link to verify your account!')
        except Exception as e:
            messages.error(request, f'Error sending email: {str(e)}')
            user.delete()  # Delete user if email fails
            return redirect('register')
        
        return redirect('register')
    
    return render(request, 'accounts/register.html')

def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, 'Invalid or expired magic link')
        return redirect('register')
    
    # Verify token
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        auth_login(request, user)
        messages.success(request, f'Welcome, {user.email}! Your account is now verified.')
        return redirect('dashboard')
    else:
        messages.error(request, 'Invalid or expired magic link')
        return redirect('register')

@login_required(login_url='register')
def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required(login_url='register')
def profile(request):
    from .models import UserProfile
    
    # Get or create profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        bio = request.POST.get('bio', '').strip()
        
        # Check if email is already taken by another user
        if email != request.user.email and User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already in use.')
            return redirect('profile')
        
        try:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            request.user.save()
            
            profile.phone = phone
            profile.bio = bio
            
            # Handle profile picture upload
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            
            profile.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')
            return redirect('profile')
    
    context = {
        'user': request.user,
        'profile': profile
    }
    return render(request, 'accounts/profile.html', context)

@login_required(login_url='register')
def dashboard(request):
    """User dashboard with property listings"""
    from houses.models import House
    from booking.models import Booking
    
    # Get landlord's properties
    properties = House.objects.filter(landlord=request.user).order_by('-created_at')
    
    # Check if user is a landlord (has properties)
    is_landlord = properties.exists()
    
    # Get tenant bookings
    tenant_bookings = Booking.objects.filter(tenant=request.user).order_by('-created_at')
    
    # Get landlord bookings (bookings for their properties)
    landlord_bookings = Booking.objects.filter(property__landlord=request.user).order_by('-created_at')
    
    # Get stats
    stats = {
        'total_properties': properties.count(),
        'available_properties': properties.filter(is_available=True).count(),
        'total_photos': sum(p.images.count() for p in properties),
        'tenant_bookings': tenant_bookings.count(),
        'pending_tenant_bookings': tenant_bookings.filter(status='pending').count(),
        'approved_tenant_bookings': tenant_bookings.filter(status='approved').count(),
        'landlord_bookings': landlord_bookings.count(),
        'pending_landlord_bookings': landlord_bookings.filter(status='pending').count(),
    }
    
    context = {
        'properties': properties,
        'stats': stats,
        'is_landlord': is_landlord,
        'recent_tenant_bookings': tenant_bookings[:3],
        'recent_landlord_bookings': landlord_bookings[:3],
    }
    return render(request, 'accounts/dashboard.html', context)
