"""
Contact Message Admin Configuration

This module handles the admin interface for contact form submissions.
These messages come from the public-facing contact page and represent
inquiries, questions, or feedback from site visitors.

The admin interface helps staff:
- Track which messages have been read vs unread
- Identify which messages have received responses
- Search through message history
- Prioritize responses based on submission date
"""

from django.contrib import admin
from ..models import ContactMessage


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """
    Admin interface for contact form messages.
    
    Contact messages represent communication from the public. Unlike adoption
    applications which follow a structured workflow, these messages can be
    about anything - general questions, specific pet inquiries, feedback,
    complaints, or partnership opportunities.
    
    The interface is designed to help staff quickly identify new messages
    and track response status to ensure no inquiry goes unanswered.
    """
    
    # List view shows key information for triaging messages
    list_display = (
        'name',           # Who sent the message
        'email',          # How to reply
        'subject',        # Quick preview of topic
        'is_read',        # Has staff seen this yet?
        'is_responded',   # Has someone replied?
        'created_at'      # When it was sent (for prioritization)
    )
    
    # Filters help staff find specific types of messages
    list_filter = (
        'is_read',        # Find unread messages quickly (highest priority)
        'is_responded',   # Find messages awaiting response
        'created_at'      # Filter by date range
    )
    
    # Search across all text fields in the message
    search_fields = (
        'name',           # Search by sender name
        'email',          # Search by email address
        'subject',        # Search in subject line
        'message'         # Search within message body
    )
    
    # Date hierarchy helps find messages from specific time periods
    date_hierarchy = 'created_at'
    
    # Default ordering - newest messages first (most urgent)
    ordering = ('-created_at',)
    
    # Created timestamp should never be edited - preserves accurate history
    readonly_fields = ('created_at',)