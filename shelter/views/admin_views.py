from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse

from ..models import Pet, AdoptionApplication, ContactMessage
from .utils import is_admin_user


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