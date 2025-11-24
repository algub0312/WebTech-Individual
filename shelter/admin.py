from django.contrib import admin
from .models import Pet, AdoptionApplication, ContactMessage, SuccessStory


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'breed', 'age', 'gender', 'status', 'featured', 'arrival_date')
    list_filter = ('type', 'size', 'gender', 'status', 'featured', 'special_needs')
    search_fields = ('name', 'breed', 'description')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'arrival_date'
    ordering = ('-arrival_date',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'type', 'breed', 'age', 'gender', 'size', 'color')
        }),
        ('Description', {
            'fields': ('description', 'personality')
        }),
        ('Medical Information', {
            'fields': ('vaccinated', 'spayed_neutered', 'microchipped', 
                      'special_needs', 'special_needs_description')
        }),
        ('Images', {
            'fields': ('main_image', 'image_2', 'image_3')
        }),
        ('Status & Fees', {
            'fields': ('status', 'arrival_date', 'adoption_fee', 'featured')
        }),
    )


@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant_name', 'pet', 'email', 'phone', 'status', 'submitted_at')
    list_filter = ('status', 'submitted_at', 'housing_type', 'has_other_pets')
    search_fields = ('first_name', 'last_name', 'email', 'pet__name')
    date_hierarchy = 'submitted_at'
    ordering = ('-submitted_at',)
    readonly_fields = ('submitted_at',)
    
    def applicant_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    applicant_name.short_description = 'Applicant'
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address')
        }),
        ('Pet Selection', {
            'fields': ('pet',)
        }),
        ('Housing Information', {
            'fields': ('housing_type', 'own_or_rent', 'landlord_approval')
        }),
        ('Household Information', {
            'fields': ('household_adults', 'household_children', 
                      'has_other_pets', 'other_pets_description')
        }),
        ('Experience & Reason', {
            'fields': ('previous_pet_experience', 'reason_for_adoption')
        }),
        ('Application Status', {
            'fields': ('status', 'submitted_at', 'reviewed_at', 'notes')
        }),
    )


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'is_read', 'is_responded', 'created_at')
    list_filter = ('is_read', 'is_responded', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)


@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'adopter_name', 'pet', 'adoption_date', 'featured')
    list_filter = ('featured', 'adoption_date')
    search_fields = ('title', 'adopter_name', 'story')
    date_hierarchy = 'adoption_date'
    ordering = ('-adoption_date',)

