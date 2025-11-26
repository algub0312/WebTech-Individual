"""
Pet Admin Configuration

This module contains the Django admin configuration for the Pet model.
PetAdmin is the most complex admin in our application because pets have
many attributes (basic info, medical info, images, status) that need to
be organized clearly for shelter staff to manage efficiently.
"""

from django.contrib import admin
from ..models import Pet


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    """
    Admin interface configuration for Pet model.
    
    The fieldsets organization mirrors the logical grouping of pet information:
    - Basic Information: Core identification details
    - Description: Narrative information about personality and behavior  
    - Medical Information: Health and care requirements
    - Images: Visual representation (main image plus additional photos)
    - Status & Fees: Availability tracking and adoption costs
    
    This organization helps shelter staff quickly find and update the information
    they need without being overwhelmed by all fields at once.
    """
    
    # List view configuration - what columns appear in the pet list
    list_display = (
        'name',           # Pet's name - primary identifier
        'type',           # Dog/Cat/Rabbit/Bird - helps quick filtering
        'breed',          # Specific breed information
        'age',            # Age helps match with adopter preferences
        'gender',         # Gender preference is common in adoption
        'status',         # Critical: available/pending/adopted
        'featured',       # Whether pet appears on homepage
        'arrival_date'    # How long pet has been at shelter
    )
    
    # Filters in sidebar - allows staff to quickly narrow down pet list
    list_filter = (
        'type',           # Filter by animal type (most common filter)
        'size',           # Small/Medium/Large
        'gender',         # Male/Female
        'status',         # Available/Pending/Adopted (very important)
        'featured',       # Find featured pets quickly
        'special_needs'   # Identify special needs animals
    )
    
    # Search functionality - staff can search by these fields
    search_fields = (
        'name',           # Search by pet name
        'breed',          # Search by breed
        'description'     # Search within description text
    )
    
    # Auto-generate slug from name - saves time during data entry
    prepopulated_fields = {'slug': ('name',)}
    
    # Date hierarchy at top of list - helps find pets by arrival period
    date_hierarchy = 'arrival_date'
    
    # Default ordering - newest arrivals first
    ordering = ('-arrival_date',)