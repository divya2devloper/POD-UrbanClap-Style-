from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.contrib import messages
from .models import Booking, BookingPing
from apps.accounts.models import PhotographerProfile


@login_required
def job_feed(request):
    """Job feed dashboard for photographers showing available bookings."""
    if request.user.user_type == 'customer':
        return redirect('bookings:create_booking')

    try:
        photographer = request.user.photographer_profile
    except PhotographerProfile.DoesNotExist:
        messages.error(request, "You need a photographer profile to access this page.")
        return redirect('accounts:profile_setup')

    pinged_booking_ids = BookingPing.objects.filter(
        photographer=photographer
    ).values_list('booking_id', flat=True)

    available_bookings = Booking.objects.filter(
        id__in=pinged_booking_ids,
        status='Pending'
    ).order_by('-created_at')

    return render(request, 'bookings/job_feed.html', {
        'bookings': available_bookings,
        'photographer': photographer,
    })


@login_required
def accept_job(request, booking_id):
    """Atomic job acceptance view with anti-race condition logic."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        photographer = request.user.photographer_profile
    except PhotographerProfile.DoesNotExist:
        return JsonResponse({'error': 'Photographer profile not found'}, status=403)

    try:
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(id=booking_id)

            if booking.status != 'Pending':
                return JsonResponse({
                    'success': False,
                    'message': 'Job already taken'
                }, status=409)

            booking.status = 'Assigned'
            booking.photographer = photographer
            booking.save(update_fields=['status', 'photographer', 'updated_at'])

            BookingPing.objects.filter(
                booking=booking,
                photographer=photographer
            ).update(was_accepted=True)

            return JsonResponse({
                'success': True,
                'message': f'Job #{booking.id} accepted successfully!',
                'booking_id': booking.id,
            })

    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)


@login_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'bookings/booking_detail.html', {'booking': booking})


@login_required
def create_booking(request):
    """Allow customers to create a new booking."""
    from .utils import get_area_coordinates, get_coordinates_for_area
    from apps.services.models import SERVICE_PACKAGES
    areas = get_area_coordinates()

    if request.method == 'POST':
        area_name = request.POST.get('area')
        coords = get_coordinates_for_area(area_name)

        if not coords:
            messages.error(request, 'Invalid area selected.')
            return render(request, 'bookings/create_booking.html', {'areas': areas, 'service_packages': SERVICE_PACKAGES})

        lat, lon = coords
        booking = Booking.objects.create(
            customer=request.user,
            service_name=request.POST.get('service_name'),
            description=request.POST.get('description', ''),
            customer_latitude=lat,
            customer_longitude=lon,
            customer_address=f"{area_name}, Ahmedabad/Gandhinagar",
            scheduled_at=request.POST.get('scheduled_at'),
            budget=request.POST.get('budget') or None,
        )
        messages.success(request, f'Booking #{booking.id} created! Searching for photographers...')
        return redirect('bookings:booking_detail', booking_id=booking.id)

    from apps.services.models import SERVICE_PACKAGES
    return render(request, 'bookings/create_booking.html', {
        'areas': areas,
        'service_packages': SERVICE_PACKAGES,
    })
