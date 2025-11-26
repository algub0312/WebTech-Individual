"""
Success Story Admin Configuration

This module configures the admin interface for adoption success stories.
Success stories are feel-good content that celebrates completed adoptions
and helps promote the shelter by showing positive outcomes.

These stories serve multiple purposes:
- Provide social proof to potential adopters
- Celebrate happy endings for staff morale
- Create shareable content for marketing
- Document the shelter's impact over time
"""

from django.contrib import admin
from ..models import SuccessStory


@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    """
    Admin interface for success stories.
    
    Success stories are testimonials from adopters about their experience
    and how their adopted pet has enriched their life. They're powerful
    marketing tools and morale boosters for shelter staff.
    
    The 'featured' flag allows staff to highlight the best stories on
    the homepage, while the date hierarchy helps browse the shelter's
    success history over time.
    """
    
    # List view shows the key elements of each story
    list_display = (
        'title',          # Story headline (e.g., "Max found his forever home!")
        'adopter_name',   # Who adopted the pet
        'pet',            # Which pet was adopted (may be None if pet deleted)
        'adoption_date',  # When the adoption occurred
        'featured'        # Whether this story appears on homepage
    )
    
    # Simple filtering - featured status and date are most relevant
    list_filter = (
        'featured',       # Find featured stories to review/rotate
        'adoption_date'   # Filter by when adoption happened
    )
    
    # Search across all text content in the story
    search_fields = (
        'title',          # Search in story title
        'adopter_name',   # Search by adopter name
        'story'           # Search within story text
    )
    
    # Date hierarchy lets staff browse success stories by time period
    # This is nice for annual reports or looking back at specific periods
    date_hierarchy = 'adoption_date'
    
    # Default ordering - newest success stories first
    ordering = ('-adoption_date',)