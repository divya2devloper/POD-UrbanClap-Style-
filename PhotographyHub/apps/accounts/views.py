from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import WhatsAppForm, PhotographerProfileForm, PortfolioItemForm
from .models import PhotographerProfile, UserProfile, PortfolioItem
from apps.bookings.models import Category

def photographer_join(request):
    """
    Landing page for photographers to join the platform.
    """
    return render(request, "accounts/photographer_join.html")


def login_view(request):
    """
    Customer portal login page.
    """
    return render(request, "accounts/login.html")

@login_required
def whatsapp_setup(request):
    """
    Setup WhatsApp number for the user after login.
    """
    profile = request.user.profile
    if request.method == 'POST':
        form = WhatsAppForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            next_url = request.GET.get('next', '/')
            return redirect(next_url)
    else:
        form = WhatsAppForm(instance=profile)
    
    return render(request, 'accounts/whatsapp_setup.html', {'form': form})

@login_required
def photographer_profile_edit(request):
    """
    Full CRUD access for photographer to manage their own profile, expertise, and portfolio.
    """
    profile, created = PhotographerProfile.objects.get_or_create(
        user=request.user,
        defaults={'base_latitude': 23.0225, 'base_longitude': 72.5714, 'max_travel_radius': 50}
    )
    
    portfolio_form = PortfolioItemForm()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # 1. Update Core Profile
        if action == 'update_profile':
            form = PhotographerProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                messages.success(request, "Professional profile & expertise updated!")
                return redirect('photographer-profile-edit')
        
        # 2. Upload Portfolio Item
        elif action == 'upload_portfolio':
            p_form = PortfolioItemForm(request.POST, request.FILES)
            if p_form.is_valid():
                category = p_form.cleaned_data['category']
                if profile.can_add_to_category(category):
                    item = p_form.save(commit=False)
                    item.photographer = profile
                    item.save()
                    messages.success(request, f"Added to {category.name} portfolio!")
                else:
                    messages.error(request, f"Limit reached: Max 10 items allowed per category.")
                return redirect('photographer-profile-edit')
        
        # 3. Delete Portfolio Item
        elif action == 'delete_portfolio':
            item_id = request.POST.get('item_id')
            item = get_object_or_404(PortfolioItem, id=item_id, photographer=profile)
            item.delete()
            messages.success(request, "Portfolio item removed.")
            return redirect('photographer-profile-edit')

    # Data for the template
    form = PhotographerProfileForm(instance=profile)
    portfolio_items = profile.portfolio_items.all().select_related('category')
    
    # Pre-calculate category data to avoid calling methods in template
    category_data = []
    for cat in Category.objects.all():
        cat_items = [item for item in portfolio_items if item.category_id == cat.id]
        category_data.append({
            'obj': cat,
            'items': cat_items,
            'count': len(cat_items)
        })
    
    return render(request, 'accounts/photographer_profile_edit.html', {
        'form': form,
        'portfolio_form': portfolio_form,
        'profile': profile,
        'category_data': category_data
    })

@login_required
def upgrade_to_premium(request):
    """
    Simulated premium upgrade for photographers.
    """
    profile = get_object_or_404(PhotographerProfile, user=request.user)
    
    if request.method == 'POST':
        # Simulate payment success
        profile.is_premium_partner = True
        profile.save()
        messages.success(request, "Welcome to the Premium Tier! You now have 10-minute priority access to all jobs.")
        return redirect('photographer-dashboard')
        
    return render(request, 'accounts/upgrade_premium.html', {'profile': profile})
