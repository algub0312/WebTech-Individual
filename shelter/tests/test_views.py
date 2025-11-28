"""
View Tests for PawHaven Shelter Application

These tests verify that our views handle HTTP requests correctly,
return appropriate responses, use correct templates, and pass
proper context data to those templates.

We test both successful scenarios (happy path) and error cases
(pets not found, invalid data, etc.)
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from shelter.models import Pet, AdoptionApplication, ContactMessage, SuccessStory
from django.contrib.auth.models import User


class PublicViewTests(TestCase):
    """
    Tests for views accessible to all users without authentication.
    
    These are the public-facing pages that form the main website
    visitors see when they come to PawHaven. We need to ensure
    they load correctly, display the right information, and handle
    edge cases gracefully.
    """
    
    def setUp(self):
        """
        Create test data used across multiple tests.
        
        We create sample pets with different statuses and characteristics
        so we can verify that views filter and display them correctly.
        The Client object simulates a web browser for making requests.
        """
        self.client = Client()
        
        # Create an available pet that should appear in listings
        self.available_pet = Pet.objects.create(
            name="Buddy",
            slug="buddy",
            type="dog",
            breed="Labrador",
            age="2 years",
            gender="Male",
            size="Large",
            color="Yellow",
            description="Friendly family dog.",
            personality=["Friendly", "Playful"],
            vaccinated=True,
            spayed_neutered=True,
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("200.00"),
            featured=True  # Featured pets appear on homepage
        )
        
        # Create an adopted pet that should NOT appear in available listings
        self.adopted_pet = Pet.objects.create(
            name="Luna",
            slug="luna",
            type="cat",
            breed="Siamese",
            age="3 years",
            gender="Female",
            size="Small",
            color="Cream",
            description="Already found her forever home!",
            personality=["Affectionate"],
            status="adopted",  # This pet should be filtered out
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("150.00"),
            featured=False
        )
        
        # Create a non-featured available pet
        self.regular_pet = Pet.objects.create(
            name="Charlie",
            slug="charlie",
            type="dog",
            breed="Beagle",
            age="5 years",
            gender="Male",
            size="Medium",
            color="Tri-color",
            description="Calm senior dog.",
            personality=["Calm", "Gentle"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("180.00"),
            featured=False  # Not featured, but still available
        )
    
    def test_homepage_loads_successfully(self):
        """
        Test that the homepage loads with HTTP 200 OK status.
        
        This is the most basic test - can users even access our site?
        A 200 status means the page loaded successfully. Any other
        status (404, 500, etc.) would indicate a problem.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_homepage_uses_correct_template(self):
        """
        Test that homepage uses the correct template file.
        
        Django's template system allows you to change templates easily,
        but you need to ensure the right template is being used for
        each view. This test catches if someone accidentally changes
        the template reference.
        """
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'shelter/index.html')
    
    def test_homepage_shows_featured_pets(self):
        """
        Test that homepage context includes only featured available pets.
        
        Business rule: Homepage should showcase featured pets to grab
        visitor attention. We verify that:
        1. Featured available pets ARE included
        2. Non-featured pets are NOT included
        3. Adopted pets are NOT included (even if featured)
        """
        response = self.client.get(reverse('home'))
        
        # Check that 'featured_pets' is in the context
        self.assertIn('featured_pets', response.context)
        
        featured_pets = response.context['featured_pets']
        
        # Buddy is featured and available - should be included
        self.assertIn(self.available_pet, featured_pets)
        
        # Luna is adopted - should NOT be included even if featured
        self.assertNotIn(self.adopted_pet, featured_pets)
        
        # Charlie is not featured - should NOT be included
        self.assertNotIn(self.regular_pet, featured_pets)
    
    def test_homepage_displays_statistics(self):
        """
        Test that homepage context includes statistics for display.
        
        The homepage shows impressive numbers (pets adopted, available now, etc.)
        to build credibility. We verify this data is passed to the template.
        """
        response = self.client.get(reverse('home'))
        
        # Stats should be in context
        self.assertIn('stats', response.context)
        
        stats = response.context['stats']
        
        # Verify stats dictionary has expected keys
        self.assertIn('total_adopted', stats)
        self.assertIn('available_now', stats)
        self.assertIn('happy_families', stats)
        self.assertIn('years_of_service', stats)
        
        # Verify available_now reflects our test data (2 available pets)
        self.assertEqual(stats['available_now'], 2)
    
    def test_pets_list_view_loads(self):
        """
        Test that the pets listing page loads successfully.
        
        This is the main page where visitors browse all available pets.
        It's critical that this page works correctly.
        """
        response = self.client.get(reverse('pets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/pets.html')
    
    def test_pets_list_shows_only_available(self):
        """
        Test that pets list shows only available pets, not adopted ones.
        
        Business rule: Visitors should only see pets they can actually adopt.
        Showing adopted pets would be confusing and frustrating.
        """
        response = self.client.get(reverse('pets'))
        
        pets = response.context['pets']
        
        # Available pets should be in the list
        self.assertIn(self.available_pet, pets)
        self.assertIn(self.regular_pet, pets)
        
        # Adopted pet should NOT be in the list
        self.assertNotIn(self.adopted_pet, pets)
    
    def test_pets_list_search_functionality(self):
        """
        Test that search filtering works on pets list.
        
        Users should be able to search by pet name or breed to find
        specific pets quickly. This tests the search query parameter.
        """
        # Search for "Labrador" should return Buddy
        response = self.client.get(reverse('pets'), {'search': 'Labrador'})
        pets = response.context['pets']
        
        self.assertIn(self.available_pet, pets)  # Buddy is a Labrador
        self.assertNotIn(self.regular_pet, pets)  # Charlie is a Beagle
    
    def test_pets_list_filter_by_type(self):
        """
        Test that filtering by pet type works correctly.
        
        Users often know what type of animal they want (dog vs cat).
        This filter helps them narrow down options quickly.
        """
        # Filter for dogs only
        response = self.client.get(reverse('pets'), {'type': 'dog'})
        pets = response.context['pets']
        
        # Buddy and Charlie are dogs - should be included
        self.assertIn(self.available_pet, pets)
        self.assertIn(self.regular_pet, pets)
        
        # Luna is a cat - should NOT be included
        # (she's also adopted, but type filter should exclude her anyway)
    
    def test_pet_detail_view_loads(self):
        """
        Test that individual pet detail page loads correctly.
        
        When a user clicks on a pet, they should see detailed information
        about that specific pet. This tests the detail view.
        """
        url = reverse('pet_detail', kwargs={
            'pk': self.available_pet.pk,
            'slug': self.available_pet.slug
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/pet_detail.html')
    
    def test_pet_detail_view_shows_correct_pet(self):
        """
        Test that pet detail page displays the requested pet's information.
        
        We need to verify that the correct pet object is passed to the template
        and that related pets suggestions are also provided.
        """
        url = reverse('pet_detail', kwargs={
            'pk': self.available_pet.pk,
            'slug': self.available_pet.slug
        })
        response = self.client.get(url)
        
        # The 'pet' context variable should be our Buddy
        self.assertEqual(response.context['pet'], self.available_pet)
        
        # Related pets should be suggested (same type, different pet)
        self.assertIn('related_pets', response.context)
    
    def test_pet_detail_nonexistent_pet_returns_404(self):
        """
        Test that requesting a non-existent pet returns 404 Not Found.
        
        Error handling test: If someone tries to access a pet that doesn't
        exist (maybe the URL was mistyped or the pet was deleted), they
        should get a proper 404 error page, not a crash.
        """
        url = reverse('pet_detail', kwargs={
            'pk': 99999,  # This pet ID doesn't exist
            'slug': 'nonexistent-pet'
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)
    
    def test_about_page_loads(self):
        """
        Test that the About Us page loads correctly.
        
        Basic smoke test for informational pages.
        """
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/about.html')
    
    def test_contact_page_loads(self):
        """
        Test that the Contact page loads correctly.
        """
        response = self.client.get(reverse('contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/contact.html')
    
    def test_contact_form_submission(self):
        """
        Test that submitting the contact form creates a ContactMessage.
        
        This is an integration test - it verifies that the entire workflow
        of submitting a contact form works: receiving POST data, validating it,
        creating a database record, and redirecting the user.
        """
        contact_data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'phone': '555-1234',
            'subject': 'Question about adoption',
            'message': 'I would like to know more about the adoption process.'
        }
        
        response = self.client.post(reverse('contact'), contact_data)
        
        # Should redirect after successful submission
        self.assertEqual(response.status_code, 302)
        
        # Verify a ContactMessage was created in database
        self.assertEqual(ContactMessage.objects.count(), 1)
        
        # Verify the message contains correct data
        message = ContactMessage.objects.first()
        self.assertEqual(message.name, 'John Doe')
        self.assertEqual(message.email, 'john@example.com')
        self.assertEqual(message.subject, 'Question about adoption')
    
    def test_success_stories_page_loads(self):
        """
        Test that the Success Stories page loads correctly.
        """
        response = self.client.get(reverse('success_stories'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/success.html')
    
    def test_adoption_process_page_loads(self):
        """
        Test that the Adoption Process information page loads.
        
        This page explains how adoption works - critical for converting
        visitors into adopters.
        """
        response = self.client.get(reverse('adoption_process'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/adoption.html')

class AuthenticatedViewTests(TestCase):
    """
    Tests for views that require user authentication.
    
    These views are protected - they require a logged-in user to access.
    We test both that authentication is enforced (unauthenticated users
    are redirected) and that authenticated users see the correct content.
    """
    
    def setUp(self):
        """
        Create a test user and pet for adoption application tests.
        
        We need a real User object to test authenticated views.
        Django's Client has a login() method that simulates logging in.
        """
        self.client = Client()
        
        # Create a regular user (not staff)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create an available pet for adoption tests
        self.pet = Pet.objects.create(
            name="Rocky",
            slug="rocky",
            type="dog",
            breed="German Shepherd",
            age="4 years",
            gender="Male",
            size="Large",
            color="Black and Tan",
            description="Loyal and protective.",
            personality=["Loyal", "Protective"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("220.00")
        )
    
    def test_account_page_requires_login(self):
        """
        Test that unauthenticated users cannot access account page.
        
        Security test: The account page shows personal information.
        Unauthenticated users should be redirected to login page.
        """
        response = self.client.get(reverse('account'))
        
        # Should redirect to login (302 status)
        self.assertEqual(response.status_code, 302)
        
        # Should redirect to login URL
        self.assertIn('/login/', response.url)
    
    def test_account_page_loads_for_authenticated_user(self):
        """
        Test that logged-in users can access their account page.
        
        After logging in, users should see their account dashboard.
        """
        # Log in as our test user
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('account'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/account.html')
    
    def test_account_page_shows_user_info(self):
        """
        Test that account page displays user's information correctly.
        
        The page should show the logged-in user's name, email, etc.
        """
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('account'))
        
        # The user object should be in context
        self.assertEqual(response.context['user'].username, 'testuser')
        self.assertEqual(response.context['user'].email, 'test@example.com')
    
    def test_user_applications_page_requires_login(self):
        """
        Test that applications page requires authentication.
        """
        response = self.client.get(reverse('user_applications'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_user_applications_shows_only_user_applications(self):
        """
        Test that users see only their own applications, not others'.
        
        Privacy test: User A should not see User B's applications.
        """
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        
        # Create application for our main user
        my_application = AdoptionApplication.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            email='test@example.com',
            phone='555-0001',
            address='123 Test St',
            pet=self.pet,
            housing_type='house',
            own_or_rent='own',
            household_adults=2,
            previous_pet_experience='Had dogs before',
            reason_for_adoption='Looking for a companion'
        )
        
        # Create application for other user
        other_application = AdoptionApplication.objects.create(
            user=other_user,
            first_name='Other',
            last_name='User',
            email='other@example.com',
            phone='555-0002',
            address='456 Other St',
            pet=self.pet,
            housing_type='apartment',
            own_or_rent='rent',
            household_adults=1,
            previous_pet_experience='First pet',
            reason_for_adoption='Want a pet'
        )
        
        # Login as main user
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('user_applications'))
        applications = response.context['applications']
        
        # Should see own application
        self.assertIn(my_application, applications)
        
        # Should NOT see other user's application
        self.assertNotIn(other_application, applications)
    
    def test_adoption_application_requires_login(self):
        """
        Test that the adoption application form requires login.
        
        Business rule: Only registered users can submit adoption applications.
        This helps prevent spam and ensures we can contact applicants.
        """
        url = reverse('adoption_application_pet', kwargs={'pet_id': self.pet.id})
        response = self.client.get(url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_adoption_application_submission_creates_application(self):
        """
        Test that submitting adoption form creates an AdoptionApplication.
        
        This is a critical integration test - it verifies the entire
        adoption application workflow works correctly.
        """
        self.client.login(username='testuser', password='testpass123')
        
        application_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone': '555-1234',
            'address': '123 Main St, City, State 12345',
            'housing_type': 'house',
            'own_or_rent': 'own',
            'landlord_approval': 'no',  # Owns, so doesn't need approval
            'household_adults': '2',
            'household_children': '1',
            'has_other_pets': 'no',
            'other_pets_description': '',
            'previous_pet_experience': 'We had a dog for 10 years who passed away last year.',
            'reason_for_adoption': 'We are ready to welcome a new family member.'
        }
        
        url = reverse('adoption_application_pet', kwargs={'pet_id': self.pet.id})
        response = self.client.post(url, application_data)
        
        # Should redirect after successful submission
        self.assertEqual(response.status_code, 302)
        
        # Verify application was created
        self.assertEqual(AdoptionApplication.objects.count(), 1)
        
        application = AdoptionApplication.objects.first()
        
        # Verify it's linked to the correct user and pet
        self.assertEqual(application.user, self.user)
        self.assertEqual(application.pet, self.pet)
        
        # Verify default status is pending
        self.assertEqual(application.status, 'pending')
    
    def test_edit_profile_requires_login(self):
        """
        Test that profile editing requires authentication.
        """
        response = self.client.get(reverse('edit_profile'))
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_edit_profile_updates_user_info(self):
        """
        Test that profile editing actually updates user information.
        
        Integration test: Submit form with new data, verify user
        object in database was updated.
        """
        self.client.login(username='testuser', password='testpass123')
        
        updated_data = {
            'username': 'testuser',  # Username shouldn't change
            'email': 'newemail@example.com',  # New email
            'first_name': 'Updated',  # New first name
            'last_name': 'Name'  # New last name
        }
        
        response = self.client.post(reverse('edit_profile'), updated_data)
        
        # Should redirect to account page after successful update
        self.assertEqual(response.status_code, 302)
        
        # Refresh user from database to get updated data
        self.user.refresh_from_db()
        
        # Verify updates were saved
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')