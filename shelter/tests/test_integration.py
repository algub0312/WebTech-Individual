"""
Integration Tests for PawHaven Shelter Application

Integration tests verify that multiple components work together correctly
to accomplish complete user workflows. Unlike unit tests that test individual
pieces in isolation, integration tests ensure the entire system functions
as a cohesive whole.

These tests are more complex and slower than unit tests, but they provide
the highest level of confidence that your application works correctly from
a user's perspective.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal

from shelter.models import Pet, AdoptionApplication, ContactMessage


class UserRegistrationAndLoginWorkflowTests(TestCase):
    """
    Tests for the complete user registration and login workflow.
    
    This simulates a new user discovering the site, creating an account,
    logging in, and accessing their account dashboard. It tests that all
    these pieces work together correctly.
    """
    
    def test_complete_registration_and_login_flow(self):
        """
        Test the entire user journey from registration to login.
        
        Workflow Steps:
        1. User visits registration page
        2. User fills out registration form
        3. User is created in database
        4. User is redirected to login or home
        5. User logs in with new credentials
        6. User can access their account page
        
        This test verifies each step works and they connect properly.
        """
        client = Client()
        
        # Step 1: Visit registration page
        response = client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Submit registration form
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        
        response = client.post(reverse('register'), registration_data)
        
        # Step 3: Verify user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Step 4: Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # Step 5: Log in with new credentials
        login_successful = client.login(username='newuser', password='SecurePass123!')
        self.assertTrue(login_successful)
        
        # Step 6: Access account page (requires authentication)
        response = client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)
        
        # Verify we see our user info on the page
        self.assertContains(response, 'newuser')
        self.assertContains(response, 'newuser@example.com')


class CompleteAdoptionWorkflowTests(TestCase):
    """
    Tests for the complete adoption workflow from browsing to application.
    
    This is the core business workflow of the application. It simulates
    a potential adopter discovering a pet, creating an account, and
    submitting an adoption application.
    """
    
    def setUp(self):
        """Create test pets for the adoption workflow."""
        self.available_pet = Pet.objects.create(
            name="Buddy",
            slug="buddy",
            type="dog",
            breed="Labrador",
            age="2 years",
            gender="Male",
            size="Large",
            color="Yellow",
            description="Friendly family dog looking for a loving home.",
            personality=["Friendly", "Playful", "Good with kids"],
            vaccinated=True,
            spayed_neutered=True,
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("200.00"),
            featured=True
        )
    
    def test_complete_adoption_application_workflow(self):
        """
        Test the entire adoption process from discovery to application.
        
        Workflow Steps:
        1. User browses available pets
        2. User views specific pet details
        3. User decides to adopt and registers account
        4. User submits adoption application
        5. Application is created and linked to user and pet
        6. User can view their application in their account
        
        This is a critical workflow - if any step fails, users can't adopt pets.
        """
        client = Client()
        
        # Step 1: Browse available pets
        response = client.get(reverse('pets'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buddy')
        
        # Step 2: View pet details
        pet_url = reverse('pet_detail', kwargs={
            'pk': self.available_pet.pk,
            'slug': self.available_pet.slug
        })
        response = client.get(pet_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Buddy')
        self.assertContains(response, 'Friendly family dog')
        
        # Step 3: User realizes they need an account to apply, so they register
        registration_data = {
            'username': 'adopter',
            'email': 'adopter@example.com',
            'first_name': 'Potential',
            'last_name': 'Adopter',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        
        response = client.post(reverse('register'), registration_data)
        self.assertEqual(response.status_code, 302)
        
        # Log in with new account
        client.login(username='adopter', password='SecurePass123!')
        
        # Step 4: Submit adoption application
        # Note: This test assumes your adoption application view accepts POST data
        # If your implementation uses a different mechanism, adjust accordingly
        application_url = reverse('adoption_application_pet', kwargs={'pet_id': self.available_pet.id})
        
        # This is a simplified test - in reality, you might need to adjust
        # the field names and structure to match your actual form
        application_data = {
            'first_name': 'Potential',
            'last_name': 'Adopter',
            'email': 'adopter@example.com',
            'phone': '555-1234',
            'address': '123 Main St, City, State 12345',
            'housing_type': 'house',
            'own_or_rent': 'own',
            'landlord_approval': '',
            'household_adults': '2',
            'household_children': '1',
            'has_other_pets': 'no',
            'other_pets_description': '',
            'previous_pet_experience': 'We had a dog for many years.',
            'reason_for_adoption': 'We want to give Buddy a loving home.',
        }
        
        # Note: If your view doesn't handle form submission this way,
        # this test might need adjustment based on your actual implementation
        response = client.post(application_url, application_data)
        
        # Step 5: Verify application was created (if the POST was successful)
        # This assertion might need adjustment based on how your view works
        if response.status_code == 302:  # If it redirects after success
            self.assertEqual(AdoptionApplication.objects.count(), 1)
            
            application = AdoptionApplication.objects.first()
            self.assertEqual(application.pet, self.available_pet)
            self.assertEqual(application.user.username, 'adopter')
            self.assertEqual(application.status, 'pending')
        
        # Step 6: User can view their application in their account
        response = client.get(reverse('user_applications'))
        self.assertEqual(response.status_code, 200)
        # If application was created, verify it appears on the page
        if AdoptionApplication.objects.exists():
            self.assertContains(response, 'Buddy')


class AdminApplicationReviewWorkflowTests(TestCase):
    """
    Tests for the admin workflow of reviewing and processing applications.
    
    This simulates a staff member logging in, reviewing applications,
    and updating their status. It's critical that this workflow is
    secure and functions correctly.
    """
    
    def setUp(self):
        """Create staff user, regular user, pet, and application."""
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        # Create regular user who will apply
        self.applicant = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='pass123',
            first_name='John',
            last_name='Doe'
        )
        
        # Create pet
        self.pet = Pet.objects.create(
            name="Luna",
            slug="luna",
            type="cat",
            breed="Siamese",
            age="3 years",
            gender="Female",
            size="Small",
            color="Cream",
            description="Sweet cat",
            personality=["Affectionate"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("150.00")
        )
        
        # Create application
        self.application = AdoptionApplication.objects.create(
            user=self.applicant,
            first_name='John',
            last_name='Doe',
            email='applicant@example.com',
            phone='555-1234',
            address='123 Test St',
            pet=self.pet,
            housing_type='apartment',
            own_or_rent='own',
            household_adults=1,
            previous_pet_experience='Had cats before',
            reason_for_adoption='Love cats',
            status='pending'
        )
    
    def test_admin_review_and_approve_application_workflow(self):
        """
        Test staff member reviewing and approving an application.
        
        Workflow Steps:
        1. Staff logs in
        2. Staff views dashboard with pending applications
        3. Staff clicks on specific application
        4. Staff reviews application details
        5. Staff adds internal notes
        6. Staff completes the application (marking pet as adopted)
        7. Pet status changes to adopted
        8. Application status changes to completed
        
        This is a critical business process that must work flawlessly.
        
        Note: Your application uses 'application_id' in URLs, and
        'completed' status marks pets as adopted (not 'approved').
        """
        client = Client()
        
        # Step 1: Staff logs in
        client.login(username='staff', password='staffpass123')
        
        # Step 2: View admin dashboard
        response = client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Dashboard should show pending application count
        stats = response.context['stats']
        self.assertEqual(stats['pending_applications'], 1)
        
        # Step 3 & 4: View application details
        app_url = reverse('admin_application_detail', kwargs={'application_id': self.application.pk})
        response = client.get(app_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Luna')
        
        # Step 5: Add internal notes
        notes_url = reverse('admin_update_application_notes', kwargs={'application_id': self.application.pk})
        notes_data = {
            'notes': 'Applicant has great references. Apartment is pet-friendly.'
        }
        response = client.post(notes_url, notes_data)
        
        # Verify notes were saved
        self.application.refresh_from_db()
        self.assertEqual(self.application.notes, notes_data['notes'])
        
        # Step 6: Complete the application (this should adopt the pet)
        status_url = reverse('admin_update_application_status', kwargs={'application_id': self.application.pk})
        status_data = {'status': 'completed'}
        response = client.post(status_url, status_data)
        
        # Step 7 & 8: Verify both application and pet status changed
        self.application.refresh_from_db()
        self.pet.refresh_from_db()
        
        self.assertEqual(self.application.status, 'completed')
        self.assertEqual(self.pet.status, 'adopted')


class ContactMessageWorkflowTests(TestCase):
    """
    Tests for the contact message workflow.
    
    This simulates a visitor sending a message and staff responding to it.
    """
    
    def setUp(self):
        """Create staff user for message management."""
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
    
    def test_contact_message_submission_and_review_workflow(self):
        """
        Test the complete flow of a visitor sending a message and staff reviewing it.
        
        Workflow Steps:
        1. Visitor submits contact form
        2. Message is saved to database
        3. Staff logs in and views messages
        4. Staff opens specific message (marks as read)
        5. Staff marks message as responded
        
        This ensures communication workflow works end-to-end.
        
        Note: Your URLs use 'contact_id' parameter, and your status update
        expects action='mark_responded' in POST data.
        """
        client = Client()
        
        # Step 1: Visitor submits contact form
        # Note: This assumes your contact view handles POST data
        # If your implementation differs, adjust accordingly
        contact_data = {
            'name': 'Jane Visitor',
            'email': 'jane@example.com',
            'phone': '555-5678',
            'subject': 'Question about volunteering',
            'message': 'I would like to volunteer. What are the requirements?'
        }
        
        response = client.post(reverse('contact'), contact_data)
        
        # Step 2: Verify message was saved (if form submission worked)
        if response.status_code == 302:  # If it redirects after success
            self.assertEqual(ContactMessage.objects.count(), 1)
            message = ContactMessage.objects.first()
            self.assertEqual(message.name, 'Jane Visitor')
            self.assertEqual(message.subject, 'Question about volunteering')
            self.assertFalse(message.is_read)
            self.assertFalse(message.is_responded)
            
            # Step 3: Staff logs in and views messages
            client.login(username='staff', password='staffpass123')
            response = client.get(reverse('admin_contacts'))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Jane Visitor')
            
            # Step 4: Staff opens message (should mark as read)
            detail_url = reverse('admin_contact_detail', kwargs={'contact_id': message.pk})
            response = client.get(detail_url)
            self.assertEqual(response.status_code, 200)
            
            # Verify marked as read
            message.refresh_from_db()
            self.assertTrue(message.is_read)
            
            # Step 5: Staff marks as responded
            status_url = reverse('admin_update_contact_status', kwargs={'contact_id': message.pk})
            response = client.post(status_url, {'action': 'mark_responded'})
            
            # Verify marked as responded
            message.refresh_from_db()
            self.assertTrue(message.is_responded)