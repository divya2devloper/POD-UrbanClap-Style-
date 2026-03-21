from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, PhotographerProfile, CustomerProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('bookings:job_feed')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        user_type = request.POST.get('user_type', 'customer')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            user_type=user_type,
            phone=phone,
        )

        if user_type == 'customer':
            CustomerProfile.objects.create(user=user)

        login(request, user)
        messages.success(request, f'Welcome to PhotographyHub, {user.get_full_name() or username}!')

        if user_type == 'photographer':
            return redirect('accounts:profile_setup')
        return redirect('bookings:create_booking')

    return render(request, 'accounts/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('bookings:job_feed')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'bookings:job_feed')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:login')


@login_required
def profile_setup(request):
    """Setup photographer profile after registration."""
    if request.user.user_type != 'photographer':
        return redirect('bookings:job_feed')

    if hasattr(request.user, 'photographer_profile'):
        return redirect('bookings:job_feed')

    from apps.bookings.utils import get_area_coordinates, get_coordinates_for_area
    areas = get_area_coordinates()

    if request.method == 'POST':
        area_name = request.POST.get('area', '')
        coords = get_coordinates_for_area(area_name)

        if not coords:
            messages.error(request, 'Please select a valid area.')
            return render(request, 'accounts/profile_setup.html', {'areas': areas})

        lat, lon = coords
        PhotographerProfile.objects.create(
            user=request.user,
            base_latitude=lat,
            base_longitude=lon,
            max_travel_radius=float(request.POST.get('max_travel_radius', 20)),
            bio=request.POST.get('bio', ''),
            experience_years=int(request.POST.get('experience_years', 0)),
        )
        messages.success(request, 'Photographer profile created! You can now receive job pings.')
        return redirect('bookings:job_feed')

    return render(request, 'accounts/profile_setup.html', {'areas': areas})
