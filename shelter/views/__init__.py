"""
Views package for the shelter app.
This package organizes views into logical modules:
- public_views: Public-facing pages (home, pets, contact, etc.)
- auth_views: Authentication and user account management
- admin_views: Admin dashboard and management functions
- utils: Helper functions used across multiple modules
"""

# Import all public views
from .public_views import (
    home,
    PetListView,
    PetDetailView,
    about,
    contact,
    adoption_process,
    success_stories,
)

# Import all authentication and user account views
from .auth_views import (
    register,
    custom_logout,
    adoption_gate,
    adoption_application,
    account,
    user_applications,
    edit_profile,
)

# Import all admin views
from .admin_views import (
    admin_dashboard,
    admin_applications,
    admin_application_detail,
    admin_update_application_status,
    admin_update_application_notes,
    admin_pets,
    admin_contacts,
    admin_contact_detail,
    admin_update_contact_status,
    admin_stats_api,
)

# Import utilities (optional, but good to have available)
from .utils import is_admin_user

# Define what gets imported when someone does "from shelter.views import *"
__all__ = [
    # Public views
    'home',
    'PetListView',
    'PetDetailView',
    'about',
    'contact',
    'adoption_process',
    'success_stories',
    
    # Auth views
    'register',
    'custom_logout',
    'adoption_gate',
    'adoption_application',
    'account',
    'user_applications',
    'edit_profile',
    
    # Admin views
    'admin_dashboard',
    'admin_applications',
    'admin_application_detail',
    'admin_update_application_status',
    'admin_update_application_notes',
    'admin_pets',
    'admin_contacts',
    'admin_contact_detail',
    'admin_update_contact_status',
    'admin_stats_api',
    
    # Utils
    'is_admin_user',
]
