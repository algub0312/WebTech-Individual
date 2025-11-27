"""
Model Tests for PawHaven Shelter Application

These tests verify that our models behave correctly in isolation.
We test:
- Model creation and field validation
- Custom methods and properties
- Model relationships
- String representations
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from shelter.models import Pet, AdoptionApplication, ContactMessage, SuccessStory
from django.contrib.auth.models import User


class PetModelTest(TestCase):
    """
    Tests for the Pet model.
    
    The Pet model is core to our application - it represents animals
    available for adoption. We need to ensure all its methods work
    correctly and that it enforces business rules properly.
    """
    
    def setUp(self):
        """
        setUp runs before each test method.
        
        Here we create a standard pet that can be used by all tests.
        This prevents code duplication - instead of creating a pet
        in every single test, we create it once here.
        
        Django automatically creates a fresh test database before each
        test and destroys it after, so tests never interfere with each other.
        """
        self.pet = Pet.objects.create(
            name="Max",
            slug="max",
            type="dog",
            breed="Golden Retriever",
            age="3 years",
            gender="Male",
            size="Large",
            color="Golden",
            description="Friendly and energetic dog looking for an active family.",
            personality=["Friendly", "Energetic", "Loyal"],
            vaccinated=True,
            spayed_neutered=True,
            microchipped=True,
            special_needs=False,
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("250.00"),
            featured=False
        )
    
    def test_pet_creation(self):
        """
        Test that a pet can be created with all required fields.
        
        This is a basic smoke test - it verifies the fundamental
        operation of creating a Pet object works.
        """
        self.assertEqual(self.pet.name, "Max")
        self.assertEqual(self.pet.breed, "Golden Retriever")
        self.assertEqual(self.pet.status, "available")
        self.assertIsNotNone(self.pet.id)  # Verify it was saved to database
    
    def test_pet_string_representation(self):
        """
        Test the __str__ method returns correct format.
        
        The __str__ method is important because it's what appears in
        Django admin and in debugging. We want it to be informative.
        """
        expected = "Max (Golden Retriever)"
        self.assertEqual(str(self.pet), expected)
    
    def test_pet_get_absolute_url(self):
        """
        Test that get_absolute_url returns correct URL for pet detail page.
        
        This method is used throughout the application to link to pet pages.
        If it breaks, links will be incorrect across the site.
        """
        expected_url = f"/pet/{self.pet.pk}/{self.pet.slug}/"
        self.assertEqual(self.pet.get_absolute_url(), expected_url)
    
    def test_pet_slug_auto_generation(self):
        """
        Test that slug is auto-generated from name if not provided.
        
        Business rule: Staff shouldn't have to manually create slugs.
        The model should handle this automatically.
        """
        pet_without_slug = Pet.objects.create(
            name="Bella Rose",  # Name with space
            type="cat",
            breed="Persian",
            age="2 years",
            gender="Female",
            size="Small",
            color="White",
            description="Calm and affectionate cat.",
            personality=["Calm", "Affectionate"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("150.00")
        )
        # Slug should be auto-created as "bella-rose"
        self.assertEqual(pet_without_slug.slug, "bella-rose")
    
    def test_is_new_arrival_method(self):
        """
        Test the is_new_arrival method correctly identifies new pets.
        
        Business rule: A pet is "new" if it arrived within the last 30 days.
        This is used to display "New Arrival" badges on the website.
        """
        # Test with a pet that arrived today (should be new)
        self.assertTrue(self.pet.is_new_arrival())
        
        # Test with a pet that arrived 40 days ago (should not be new)
        old_pet = Pet.objects.create(
            name="Old Timer",
            type="dog",
            breed="Beagle",
            age="5 years",
            gender="Male",
            size="Medium",
            color="Tri-color",
            description="Been at shelter for a while.",
            personality=["Patient"],
            status="available",
            arrival_date=timezone.now().date() - timedelta(days=40),
            adoption_fee=Decimal("200.00")
        )
        self.assertFalse(old_pet.is_new_arrival())
    
    def test_get_badge_method_special_needs(self):
        """
        Test get_badge returns 'Special Needs' for special needs pets.
        
        Badge priority: Special Needs > New Arrival > None
        """
        special_needs_pet = Pet.objects.create(
            name="Charlie",
            type="dog",
            breed="Mixed",
            age="8 years",
            gender="Male",
            size="Medium",
            color="Brown",
            description="Senior dog with diabetes.",
            personality=["Gentle"],
            special_needs=True,
            special_needs_description="Requires insulin twice daily",
            status="available",
            arrival_date=timezone.now().date(),  # New arrival, but special needs takes priority
            adoption_fee=Decimal("100.00")
        )
        self.assertEqual(special_needs_pet.get_badge(), "Special Needs")
    
    def test_get_badge_method_new_arrival(self):
        """
        Test get_badge returns 'New Arrival' for recent pets without special needs.
        """
        self.assertEqual(self.pet.get_badge(), "New Arrival")
    
    def test_get_badge_method_none(self):
        """
        Test get_badge returns None for old pets without special needs.
        """
        old_normal_pet = Pet.objects.create(
            name="Oldie",
            type="cat",
            breed="Tabby",
            age="4 years",
            gender="Female",
            size="Small",
            color="Gray",
            description="Regular cat, been here a while.",
            personality=["Independent"],
            special_needs=False,
            status="available",
            arrival_date=timezone.now().date() - timedelta(days=60),
            adoption_fee=Decimal("120.00")
        )
        self.assertIsNone(old_normal_pet.get_badge())
    
    def test_get_all_images_method(self):
        """
        Test get_all_images returns list of all uploaded images.
        
        This method is used to display image galleries on pet detail pages.
        """
        # Without images (our setUp pet has none)
        self.assertEqual(len(self.pet.get_all_images()), 0)
        
        # Note: Testing with actual file uploads requires more setup
        # For now, we verify the method exists and returns a list
        self.assertIsInstance(self.pet.get_all_images(), list)