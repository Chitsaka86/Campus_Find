from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from booking.models import MoverBooking

from .models import MoverService, MoverRating


def movers_list(request):
	query = request.GET.get("q")
	cleaning = request.GET.get("cleaning")

	services = MoverService.objects.all().annotate(
		avg_rating=Avg("ratings__score"), rating_count=Count("ratings")
	)

	if query:
		services = services.filter(Q(name__icontains=query) | Q(location__icontains=query))
	if cleaning == "1":
		services = services.filter(provides_cleaning=True)

	context = {
		"services": services,
		"query": query or "",
		"cleaning": cleaning == "1",
	}
	return render(request, "movers/list.html", context)


def mover_detail(request, pk):
	service = get_object_or_404(
		MoverService.objects.annotate(
			avg_rating=Avg("ratings__score"), rating_count=Count("ratings")
		),
		pk=pk,
	)

	# Handle rating submission
	if request.method == "POST":
		if not request.user.is_authenticated:
			messages.error(request, "Please log in to leave a rating.")
			return redirect("login")
		if service.owner == request.user:
			messages.error(request, "You cannot rate your own service.")
			return redirect("mover_detail", pk=pk)

		try:
			score = int(request.POST.get("score", 0))
		except ValueError:
			score = 0
		comment = request.POST.get("comment", "").strip()

		if score < 1 or score > 5:
			messages.error(request, "Rating must be between 1 and 5.")
			return redirect("mover_detail", pk=pk)

		MoverRating.objects.update_or_create(
			service=service,
			user=request.user,
			defaults={"score": score, "comment": comment},
		)
		messages.success(request, "Thank you! Your rating has been saved.")
		return redirect("mover_detail", pk=pk)
	ratings = service.ratings.select_related("user")
	context = {"service": service, "ratings": ratings}
	return render(request, "movers/detail.html", context)


@login_required(login_url="register")
def add_mover(request):
	if request.method == "POST":
		name = request.POST.get("name", "").strip()
		description = request.POST.get("description", "").strip()
		location = request.POST.get("location", "").strip()
		phone = request.POST.get("phone", "").strip()
		email = request.POST.get("email", "").strip()
		provides_cleaning = request.POST.get("provides_cleaning") == "on"
		rate_per_km = request.POST.get("rate_per_km")

		if not all([name, description, location, phone, rate_per_km]):
			messages.error(request, "Please fill all required fields.")
			return redirect("add_mover")

		service = MoverService.objects.create(
			owner=request.user,
			name=name,
			description=description,
			location=location,
			phone=phone,
			email=email,
			provides_cleaning=provides_cleaning,
			rate_per_km=rate_per_km,
		)
		messages.success(request, "Mover service added!")
		return redirect("mover_detail", pk=service.pk)

	return render(request, "movers/add.html")



@login_required(login_url="register")
def my_mover_services(request):
    services = MoverService.objects.filter(owner=request.user).annotate(
        avg_rating=Avg("ratings__score"), rating_count=Count("ratings")
    )
    return render(request, "movers/my_services.html", {"services": services})


@login_required(login_url="register")
def edit_mover(request, pk):
    service = get_object_or_404(MoverService, pk=pk, owner=request.user)

    if request.method == "POST":
        service.name = request.POST.get("name", service.name).strip()
        service.description = request.POST.get("description", service.description).strip()
        service.location = request.POST.get("location", service.location).strip()
        service.phone = request.POST.get("phone", service.phone).strip()
        service.email = request.POST.get("email", service.email).strip()
        service.provides_cleaning = request.POST.get("provides_cleaning") == "on"
        rate_val = request.POST.get("rate_per_km")
        if rate_val:
            service.rate_per_km = rate_val
        service.save()
        messages.success(request, "Service updated.")
        return redirect("my_mover_services")

    return render(request, "movers/edit.html", {"service": service})


@login_required(login_url="register")
def manage_mover_bookings(request):
    # Only show bookings for movers owned by this user
    mover_services = MoverService.objects.filter(owner=request.user)
    bookings = MoverBooking.objects.filter(mover__in=mover_services).order_by('-created_at')
    
    if request.method == "POST":
        booking_id = request.POST.get("booking_id")
        action = request.POST.get("action")
        booking = get_object_or_404(MoverBooking, pk=booking_id, mover__in=mover_services)
        if action == "approve":
            booking.status = "confirmed"
            messages.success(request, "Booking approved!")
        elif action == "reject":
            booking.status = "rejected"
            messages.success(request, "Booking rejected!")
        booking.save()
        return redirect("manage_mover_bookings")
    
    context = {"bookings": bookings}
    return render(request, "movers/manage_bookings.html", context)
