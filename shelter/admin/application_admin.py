"""
Adoption Application Admin Configuration

This module configures how adoption applications are displayed and managed
in Django admin. Applications are the core workflow of the shelter - they
represent the connection between interested adopters and available pets.

Key features:
- Custom method to display applicant's full name
- Comprehensive filtering by status, date, and applicant details
- Read-only timestamp fields to preserve submission history
- Organized fieldsets that follow the application form structure
"""

from django.contrib import admin
from ..models import AdoptionApplication


@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    """
    Admin interface for managing adoption applications.
    
    Applications go through a workflow: pending → approved/rejected → completed.
    This admin interface is designed to help staff efficiently review applications,
    track their status, and maintain notes throughout the adoption process.
    """
    
    # List view columns
    list_display = (
        'applicant_name',  # Custom method showing full name (defined below)
        'pet',             # Which pet they're applying for
        'email',           # Contact information
        'phone',           # Alternative contact method
        'status',          # Current application status (critical for workflow)
        'submitted_at'     # When application was received
    )
    
    # Filters to help staff prioritize and organize applications
    list_filter = (
        'status',          # Most important: pending/approved/rejected/completed
        'submitted_at',    # Filter by submission date
        'housing_type',    # House/Apartment - affects pet compatibility
        'has_other_pets'   # Important for pet matching
    )
    
    # Search across applicant details and pet information
    search_fields = (
        'first_name',      # Search by applicant first name
        'last_name',       # Search by applicant last name
        'email',           # Search by email
        'pet__name'        # Search by pet name (note the double underscore for related model)
    )
    
    # Date hierarchy for finding applications by time period
    date_hierarchy = 'submitted_at'
    
    # Default ordering - newest applications first
    ordering = ('-submitted_at',)
    
    # Make submission timestamp read-only - we never want to change when it was submitted
    readonly_fields = ('submitted_at',)
    
    def applicant_name(self, obj):
        """
        Custom method to display applicant's full name in list view.
        
        This is more user-friendly than showing first_name and last_name
        in separate columns. Django admin will call this method for each
        row in the application list.
        
        Args:
            obj: The AdoptionApplication instance being displayed
            
        Returns:
            str: Full name in "First Last" format
        """
        return f"{obj.first_name} {obj.last_name}"
    
    # Configure how this custom method appears in the list
    applicant_name.short_description = 'Applicant'
    
    # Fieldsets organize the detail/edit form logically
    fieldsets = (
        ('Applicant Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address'),
            'description': 'Contact details for the potential adopter'
        }),
        ('Pet Selection', {
            'fields': ('pet',),
            'description': 'Which pet this application is for'
        }),
        ('Housing Information', {
            'fields': ('housing_type', 'own_or_rent', 'landlord_approval'),
            'description': 'Living situation - important for pet compatibility'
        }),
        ('Household Information', {
            'fields': (
                'household_adults', 
                'household_children',
                'has_other_pets', 
                'other_pets_description'
            ),
            'description': 'Family composition and existing pets'
        }),
        ('Experience & Reason', {
            'fields': ('previous_pet_experience', 'reason_for_adoption'),
            'description': 'Applicant background and motivation'
        }),
        ('Application Status', {
            'fields': ('status', 'submitted_at', 'reviewed_at', 'notes'),
            'description': 'Application workflow tracking and staff notes'
        }),
    )