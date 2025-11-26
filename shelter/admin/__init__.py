"""
Admin Package for Shelter Application

This package organizes Django admin configurations into separate modules,
one for each model. This modular approach makes the admin configurations
easier to find, modify, and extend as the application grows.

Organization:
- pet_admin.py: Configuration for Pet model
- application_admin.py: Configuration for AdoptionApplication model  
- message_admin.py: Configuration for ContactMessage model
- story_admin.py: Configuration for SuccessStory model

Each module uses the @admin.register() decorator, so simply importing
them here is sufficient to register them with Django's admin site.
Django will automatically discover and register all admin classes
when this package is imported.
"""

# Import all admin configurations
# The @admin.register() decorators in each module handle the registration
from .pet_admin import PetAdmin
from .application_admin import AdoptionApplicationAdmin
from .message_admin import ContactMessageAdmin
from .story_admin import SuccessStoryAdmin

# Define what gets imported with "from shelter.admin import *"
# This is more for documentation than functionality - Django doesn't
# actually need this for admin discovery, but it's good practice
__all__ = [
    'PetAdmin',
    'AdoptionApplicationAdmin',
    'ContactMessageAdmin',
    'SuccessStoryAdmin',
]
