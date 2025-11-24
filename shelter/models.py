from django.db import models
from django.utils.text import slugify
from django.urls import reverse


class Pet(models.Model):
    """Model representing a pet available for adoption"""
    
    PET_TYPES = [
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('rabbit', 'Rabbit'),
        ('bird', 'Bird'),
    ]
    
    SIZES = [
        ('Small', 'Small'),
        ('Medium', 'Medium'),
        ('Large', 'Large'),
    ]
    
    GENDERS = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending'),
        ('adopted', 'Adopted'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    type = models.CharField(max_length=20, choices=PET_TYPES)
    breed = models.CharField(max_length=100)
    age = models.CharField(max_length=50)  # e.g., "3 years", "6 months"
    gender = models.CharField(max_length=10, choices=GENDERS)
    size = models.CharField(max_length=20, choices=SIZES)
    color = models.CharField(max_length=100)
    
    # Description and Personality
    description = models.TextField()
    personality = models.JSONField(default=list)  # Store as list of traits
    
    # Medical Information
    vaccinated = models.BooleanField(default=False)
    spayed_neutered = models.BooleanField(default=False)
    microchipped = models.BooleanField(default=False)
    special_needs = models.BooleanField(default=False)
    special_needs_description = models.TextField(blank=True, null=True)
    
    # Images
    main_image = models.ImageField(upload_to='pets/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='pets/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='pets/', blank=True, null=True)
    
    # Status and Dates
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    arrival_date = models.DateField()
    adoption_fee = models.DecimalField(max_digits=10, decimal_places=2)
    featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-arrival_date', 'name']
        verbose_name = 'Pet'
        verbose_name_plural = 'Pets'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.breed})"
    
    def get_absolute_url(self):
        return reverse('pet_detail', kwargs={'pk': self.pk, 'slug': self.slug})
    
    def get_all_images(self):
        """Return list of all available images"""
        images = []
        if self.main_image:
            images.append(self.main_image)
        if self.image_2:
            images.append(self.image_2)
        if self.image_3:
            images.append(self.image_3)
        return images
    
    def is_new_arrival(self):
        """Check if pet arrived within the last 30 days"""
        from django.utils import timezone
        from datetime import timedelta
        return (timezone.now().date() - self.arrival_date).days <= 30
    
    def get_badge(self):
        """Return appropriate badge text for the pet"""
        if self.special_needs:
            return 'Special Needs'
        elif self.is_new_arrival():
            return 'New Arrival'
        return None


class AdoptionApplication(models.Model):
    """Model for adoption applications"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Adoption Completed'),
    ]
    
    # User Link (optional - for logged-in users)
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    
    # Applicant Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    
    # Pet Selection
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name='applications')
    
    # Housing Information
    housing_type = models.CharField(max_length=50)  # House, Apartment, etc.
    own_or_rent = models.CharField(max_length=20)
    landlord_approval = models.BooleanField(default=False)
    
    # Household Information
    household_adults = models.IntegerField()
    household_children = models.IntegerField(default=0)
    has_other_pets = models.BooleanField(default=False)
    other_pets_description = models.TextField(blank=True)
    
    # Experience and Commitment
    previous_pet_experience = models.TextField()
    reason_for_adoption = models.TextField()
    
    # Application Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Adoption Application'
        verbose_name_plural = 'Adoption Applications'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.pet.name}"


class ContactMessage(models.Model):
    """Model for contact form submissions"""
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    
    # Status
    is_read = models.BooleanField(default=False)
    is_responded = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class SuccessStory(models.Model):
    """Model for adoption success stories"""
    
    pet = models.ForeignKey(Pet, on_delete=models.SET_NULL, null=True, blank=True)
    adopter_name = models.CharField(max_length=100)
    adoption_date = models.DateField()
    
    title = models.CharField(max_length=200)
    story = models.TextField()
    
    image = models.ImageField(upload_to='success_stories/', blank=True, null=True)
    
    featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-adoption_date']
        verbose_name = 'Success Story'
        verbose_name_plural = 'Success Stories'
    
    def __str__(self):
        return self.title
