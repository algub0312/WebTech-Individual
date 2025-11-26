from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse

from ..models import Pet, AdoptionApplication, ContactMessage, SuccessStory


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
            'total_adopted': total_adopted or 1247,
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


def adoption_process(request):
    """Adoption process information page"""
    return render(request, 'shelter/adoption.html')


def success_stories(request):
    """Success stories page"""
    stories = SuccessStory.objects.all()
    featured_stories = stories.filter(featured=True)[:3]
    
    context = {
        'stories': stories,
        'featured_stories': featured_stories,
    }
    return render(request, 'shelter/success.html', context)