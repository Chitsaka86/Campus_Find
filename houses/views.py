from django.shortcuts import render
from .models import House

def home(request):
    stats = {
        'houses': House.objects.filter(category='house').count(),
        'hostels': House.objects.filter(category='hostel').count(),
        'apartments': House.objects.filter(category='apartment').count(),
        'roommates': House.objects.filter(category='roommate').count(),
    }
    recent_listings = House.objects.order_by('-created_at')[:10]  # Last 10 listings
    context = {
        'stats': stats,
        'recent_listings': recent_listings
    }
    return render(request, 'home.html', context)

# Create your views here.
