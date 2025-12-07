from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

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
            messages.info(request, 'If an account with this email exists, you will receive a magic link shortly.')
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
    return render(request, 'accounts/profile.html')

@login_required(login_url='register')
def dashboard(request):
    """User dashboard"""
    return render(request, 'accounts/dashboard.html')
