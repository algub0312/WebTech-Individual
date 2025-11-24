from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Pet, AdoptionApplication, ContactMessage, SuccessStory
from .forms import CustomUserCreationForm, UserUpdateForm


# Existing views (unchanged)
def home(request):
    """Homepage view with featured pets and stats"""
    featured_pets = Pet.objects.filter(featured=True, status='available')[:3]
    
    # Calculate stats
    total_adopted = Pet.objects.filter(status='adopted').count()
    available_now = Pet.objects.filter(status='available').count()
    happy_families = AdoptionApplication.objects.filter(status='completed').count()
    
    context = {
        'featured_pets': featured_pets,
        'stats': {
            'total_adopted': total_adopted or 1247,  # Use actual or fallback
            'available_now': available_now or 15,
            'happy_families': happy_families or 156,
            'years_of_service': 8,
        }
    }
    return render(request, 'shelter/index.html', context)


class PetListView(ListView):
    """View for browsing all pets with filters"""
    model = Pet
    template_name = 'shelter/pets.html'
    context_object_name = 'pets'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Pet.objects.filter(status='available')
        
        # Search
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(breed__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filter by type
        pet_type = self.request.GET.get('type')
        if pet_type and pet_type != 'all':
            queryset = queryset.filter(type=pet_type)
        
        # Filter by size
        sizes = self.request.GET.getlist('size')
        if sizes:
            queryset = queryset.filter(size__in=sizes)
        
        # Filter by special needs
        if self.request.GET.get('specialNeeds'):
            queryset = queryset.filter(special_needs=True)
        
        # Sort
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'newest':
            queryset = queryset.order_by('-arrival_date')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('arrival_date')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_pets'] = self.get_queryset().count()
        return context


class PetDetailView(DetailView):
    """View for individual pet detail page"""
    model = Pet
    template_name = 'shelter/pet_detail.html'
    context_object_name = 'pet'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get related pets (same type, different pet)
        context['related_pets'] = Pet.objects.filter(
            type=self.object.type,
            status='available'
        ).exclude(pk=self.object.pk)[:3]
        return context


def about(request):
    """About page view"""
    return render(request, 'shelter/about.html')


def contact(request):
    """Contact page view with form submission"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message_text = request.POST.get('message')
        
        # Create contact message
        contact_message = ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message_text
        )
        
        messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
        return redirect('contact')
    
    return render(request, 'shelter/contact.html')

def adoption_gate(request, pet_id=None):
    """Redirect to adoption form if logged in, otherwise to login page"""
    next_url = (
        reverse('adoption_application_pet', args=[pet_id])
        if pet_id else reverse('adoption_application')
    )

    if request.user.is_authenticated:
        return redirect(next_url)
    
    
    return redirect(f"{reverse('site_login')}?next={next_url}")

def adoption_process(request):
    """Adoption process information page"""
    return render(request, 'shelter/adoption.html')

@login_required(login_url='site_login')
def adoption_application(request, pet_id=None):
    """Adoption application form"""
    pet = None
    if pet_id:
        pet = get_object_or_404(Pet, pk=pet_id, status='available')
    
    if request.method == 'POST':
        # Get the user if authenticated, otherwise None
        user = request.user if request.user.is_authenticated else None
        
        # Get form data
        application = AdoptionApplication.objects.create(
            user=user,  # Link to user if logged in
            first_name=request.POST.get('first_name'),
            last_name=request.POST.get('last_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            pet=pet if pet else get_object_or_404(Pet, pk=request.POST.get('pet_id')),
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
        
        # If user is logged in, redirect to their applications page
        if request.user.is_authenticated:
            return redirect('user_applications')
        else:
            return redirect('pet_detail', pk=application.pet.pk, slug=application.pet.slug)
    
    context = {
        'pet': pet,
        'available_pets': Pet.objects.filter(status='available') if not pet else None
    }
    return render(request, 'shelter/adoption_application.html', context)


def success_stories(request):
    """Success stories page"""
    stories = SuccessStory.objects.all()
    featured_stories = stories.filter(featured=True)[:3]
    
    context = {
        'stories': stories,
        'featured_stories': featured_stories,
    }
    return render(request, 'shelter/success.html', context)


# Authentication Views

def register(request):
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


def custom_logout(request):
    """Custom logout view to ensure proper redirect"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


# Admin Views
def is_admin_user(user):
    """Check if user is staff/admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin_user)
def admin_dashboard(request):
    """Admin dashboard with overview statistics"""
    # Calculate statistics
    stats = {
        'pending_applications': AdoptionApplication.objects.filter(status='pending').count(),
        'available_pets': Pet.objects.filter(status='available').count(),
        'total_adopted': Pet.objects.filter(status='adopted').count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
    }
    
    # Get recent applications (last 5)
    recent_applications = AdoptionApplication.objects.select_related('pet').order_by('-submitted_at')[:5]
    
    # Get recent contact messages (last 5)
    recent_contacts = ContactMessage.objects.order_by('-created_at')[:5]
    
    context = {
        'stats': stats,
        'recent_applications': recent_applications,
        'recent_contacts': recent_contacts,
    }
    return render(request, 'shelter/admin/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_applications(request):
    """Admin view for managing all applications"""
    applications = AdoptionApplication.objects.select_related('pet').order_by('-submitted_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    # Search by applicant name, email, or pet name
    search_query = request.GET.get('search')
    if search_query:
        applications = applications.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(pet__name__icontains=search_query) |
            Q(pet__breed__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(applications, 10)  # Show 10 applications per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'applications': page_obj,
        'total_applications': applications.count(),
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    return render(request, 'shelter/admin/admin_applications.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_application_detail(request, application_id):
    """Detailed view of a single application"""
    application = get_object_or_404(AdoptionApplication, id=application_id)
    
    context = {
        'application': application,
    }
    return render(request, 'shelter/admin/admin_application_detail.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_update_application_status(request, application_id):
    """Update application status"""
    if request.method == 'POST':
        application = get_object_or_404(AdoptionApplication, id=application_id)
        new_status = request.POST.get('status')
        
        if new_status in ['pending', 'approved', 'rejected', 'completed']:
            old_status = application.status
            application.status = new_status
            application.reviewed_at = timezone.now()
            application.save()
            
            # Update pet status if application is completed
            if new_status == 'completed':
                application.pet.status = 'adopted'
                application.pet.save()
            elif old_status == 'completed' and new_status != 'completed':
                # If changing from completed to something else, make pet available again
                application.pet.status = 'available'
                application.pet.save()
            
            messages.success(request, f'Application status updated to {application.get_status_display()}')
        else:
            messages.error(request, 'Invalid status')
    
    # Redirect back to the referring page or application detail
    next_url = request.META.get('HTTP_REFERER')
    if 'admin_application_detail' in str(next_url):
        return redirect('admin_application_detail', application_id=application_id)
    else:
        return redirect('admin_applications')


@login_required
@user_passes_test(is_admin_user)
def admin_update_application_notes(request, application_id):
    """Update admin notes for an application"""
    if request.method == 'POST':
        application = get_object_or_404(AdoptionApplication, id=application_id)
        notes = request.POST.get('notes', '')
        
        application.notes = notes
        application.reviewed_at = timezone.now()
        application.save()
        
        messages.success(request, 'Notes updated successfully')
    
    return redirect('admin_application_detail', application_id=application_id)


@login_required
@user_passes_test(is_admin_user)
def admin_pets(request):
    """Admin view for managing pets"""
    pets = Pet.objects.all().prefetch_related('applications').order_by('-arrival_date')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        pets = pets.filter(status=status_filter)
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        pets = pets.filter(type=type_filter)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        pets = pets.filter(
            Q(name__icontains=search_query) |
            Q(breed__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(pets, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'pets': page_obj,
        'total_pets': pets.count(),
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    return render(request, 'shelter/admin/admin_pets.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_contacts(request):
    """Admin view for managing contact messages"""
    contacts = ContactMessage.objects.all().order_by('-created_at')
    
    # Filter by read status
    read_filter = request.GET.get('read')
    if read_filter == 'unread':
        contacts = contacts.filter(is_read=False)
    elif read_filter == 'read':
        contacts = contacts.filter(is_read=True)
    
    # Search
    search_query = request.GET.get('search')
    if search_query:
        contacts = contacts.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(subject__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(contacts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'contacts': page_obj,
        'total_contacts': contacts.count(),
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
    }
    return render(request, 'shelter/admin/admin_contacts.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_contact_detail(request, contact_id):
    """Detailed view of a contact message"""
    contact = get_object_or_404(ContactMessage, id=contact_id)
    
    # Mark as read if not already
    if not contact.is_read:
        contact.is_read = True
        contact.save()
    
    context = {
        'contact': contact,
    }
    return render(request, 'shelter/admin/admin_contact_detail.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_update_contact_status(request, contact_id):
    """Update contact message status"""
    if request.method == 'POST':
        contact = get_object_or_404(ContactMessage, id=contact_id)
        action = request.POST.get('action')
        
        if action == 'mark_responded':
            contact.is_responded = True
            contact.save()
            messages.success(request, 'Message marked as responded')
        elif action == 'mark_unresponded':
            contact.is_responded = False
            contact.save()
            messages.success(request, 'Message marked as not responded')
    
    return redirect('admin_contact_detail', contact_id=contact_id)


# Quick stats for AJAX requests
@login_required
@user_passes_test(is_admin_user)
def admin_stats_api(request):
    """API endpoint for dashboard stats"""
    stats = {
        'pending_applications': AdoptionApplication.objects.filter(status='pending').count(),
        'available_pets': Pet.objects.filter(status='available').count(),
        'total_adopted': Pet.objects.filter(status='adopted').count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'applications_this_week': AdoptionApplication.objects.filter(
            submitted_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count(),
    }
    return JsonResponse(stats)