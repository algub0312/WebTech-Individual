from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse

from ..models import Pet, AdoptionApplication
from ..forms import CustomUserCreationForm, UserUpdateForm


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('account')

    next_url = request.GET.get('next') or request.POST.get('next')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to PawHaven, {user.username}!')
            return redirect(next_url or 'account')
    else:
        form = CustomUserCreationForm()

    return render(request, 'shelter/register.html', {'form': form, 'next': next_url})


def custom_logout(request):
    """Custom logout view to ensure proper redirect"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def adoption_gate(request, pet_id=None):
    """Redirect to adoption form if logged in, otherwise to login page"""
    next_url = (
        reverse('adoption_application_pet', args=[pet_id])
        if pet_id else reverse('adoption_application')
    )

    if request.user.is_authenticated:
        return redirect(next_url)
    
    return redirect(f"{reverse('site_login')}?next={next_url}")


@login_required(login_url='site_login')
def adoption_application(request, pet_id=None):
    """Adoption application form - requires login"""
    pet = None
    if pet_id:
        pet = Pet.objects.filter(pk=pet_id, status='available').first()
        if not pet:
            messages.error(request, 'Pet not found or no longer available.')
            return redirect('pets')
    
    if request.method == 'POST':
        # Get the user if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # Get or create pet reference
        if not pet:
            pet_post_id = request.POST.get('pet_id')
            if pet_post_id:
                pet = Pet.objects.filter(pk=pet_post_id, status='available').first()
        
        if not pet:
            messages.error(request, 'Please select a valid pet.')
            return redirect('adoption_application')
        
        # Create application
        application = AdoptionApplication.objects.create(
            user=user,
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            pet=pet,
            housing_type=request.POST.get('housing_type'),
            own_or_rent=request.POST.get('own_or_rent'),
            landlord_approval=request.POST.get('landlord_approval') == 'yes',
            household_adults=request.POST.get('household_adults', 1),
            household_children=request.POST.get('household_children', 0),
            has_other_pets=request.POST.get('has_other_pets') == 'yes',
            other_pets_description=request.POST.get('other_pets_description', ''),
            previous_pet_experience=request.POST.get('previous_pet_experience'),
            reason_for_adoption=request.POST.get('reason_for_adoption'),
        )
        
        messages.success(request, 'Your application has been submitted successfully! We will review it and contact you soon.')
        
        # Redirect to user applications if logged in
        if request.user.is_authenticated:
            return redirect('user_applications')
        else:
            return redirect('pet_detail', pk=application.pet.pk, slug=application.pet.slug)
    
    context = {
        'pet': pet,
        'available_pets': Pet.objects.filter(status='available') if not pet else None
    }
    return render(request, 'shelter/adoption_application.html', context)


@login_required
def account(request):
    """User account dashboard - redirects admins to admin dashboard"""
    # Check if user is admin and redirect to admin dashboard
    if request.user.is_staff or request.user.is_superuser:
        return redirect('admin_dashboard')
    
    # Regular user logic
    recent_applications = AdoptionApplication.objects.filter(
        Q(user=request.user) | Q(email=request.user.email)
    ).order_by('-submitted_at')[:3]
    
    context = {
        'recent_applications': recent_applications,
    }
    return render(request, 'shelter/account.html', context)


@login_required
def user_applications(request):
    """View all user's adoption applications"""
    # Get applications linked to this user OR matching their email
    applications = AdoptionApplication.objects.filter(
        Q(user=request.user) | Q(email=request.user.email)
    ).order_by('-submitted_at')
    
    context = {
        'applications': applications,
    }
    return render(request, 'shelter/user_applications.html', context)


@login_required
def edit_profile(request):
    """Edit user profile information"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('account')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'shelter/edit_profile.html', {'form': form})