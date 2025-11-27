"""
Admin View Tests for PawHaven Shelter Application

These tests verify that administrative functions are properly secured
and work correctly. Admin views should only be accessible to staff users
and should handle data management operations correctly.

Security is paramount here - we must ensure unauthorized users cannot
access or modify sensitive administrative data.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth.models import User

from shelter.models import Pet, AdoptionApplication, ContactMessage


class AdminViewSecurityTests(TestCase):
    """
    Tests for admin view security and access control.
    
    These tests verify that administrative views properly enforce
    the requirement that only staff users can access them. This is
    critical for preventing unauthorized access to sensitive data.
    """
    
    def setUp(self):
        """
        Create both regular and staff users for permission testing.
        
        We need to test that staff users CAN access admin views while
        regular users CANNOT. This requires creating both types of users.
        """
        self.client = Client()
        
        # Create a regular user (not staff)
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpass123'
        )
        
        # Create a staff user (has admin access)
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True  # This flag grants admin access
        )
        
        # Create test data that admin might interact with
        self.pet = Pet.objects.create(
            name="Admin Test Pet",
            slug="admin-test-pet",
            type="dog",
            breed="Mixed",
            age="3 years",
            gender="Male",
            size="Medium",
            color="Brown",
            description="Test pet for admin operations",
            personality=["Friendly"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("150.00")
        )
        
        self.application = AdoptionApplication.objects.create(
            user=self.regular_user,
            first_name='Regular',
            last_name='User',
            email='regular@example.com',
            phone='555-0000',
            address='123 Test St',
            pet=self.pet,
            housing_type='house',
            own_or_rent='own',
            household_adults=2,
            previous_pet_experience='Some experience',
            reason_for_adoption='Want a pet',
            status='pending'
        )
    
    def test_admin_dashboard_requires_staff(self):
        """
        Test that non-staff users cannot access admin dashboard.
        
        Security test: The admin dashboard shows sensitive information
        about all applications, pets, etc. Regular users must not be
        able to access it, even if they're logged in.
        """
        # Try accessing as anonymous user
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirected to login
        
        # Try accessing as regular logged-in user
        self.client.login(username='regularuser', password='regularpass123')
        response = self.client.get(reverse('admin_dashboard'))
        # Should still be redirected (forbidden) or show 403
        self.assertIn(response.status_code, [302, 403])
    
    def test_admin_dashboard_allows_staff(self):
        """
        Test that staff users CAN access admin dashboard.
        
        Staff users need the dashboard to do their job - this verifies
        they can access it successfully.
        """
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('admin_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/admin/admin_dashboard.html')
    
    def test_admin_applications_requires_staff(self):
        """
        Test that applications management page requires staff access.
        """
        # Anonymous user
        response = self.client.get(reverse('admin_applications'))
        self.assertEqual(response.status_code, 302)
        
        # Regular user
        self.client.login(username='regularuser', password='regularpass123')
        response = self.client.get(reverse('admin_applications'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_admin_pets_requires_staff(self):
        """
        Test that pets management page requires staff access.
        """
        response = self.client.get(reverse('admin_pets'))
        self.assertEqual(response.status_code, 302)
        
        self.client.login(username='regularuser', password='regularpass123')
        response = self.client.get(reverse('admin_pets'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_admin_contacts_requires_staff(self):
        """
        Test that contact messages page requires staff access.
        
        Contact messages may contain personal information, so they
        must be protected from unauthorized access.
        """
        response = self.client.get(reverse('admin_contacts'))
        self.assertEqual(response.status_code, 302)
        
        self.client.login(username='regularuser', password='regularpass123')
        response = self.client.get(reverse('admin_contacts'))
        self.assertIn(response.status_code, [302, 403])


class AdminDashboardTests(TestCase):
    """
    Tests for admin dashboard functionality.
    
    The dashboard provides an overview of key metrics and recent activity.
    We test that it displays correct statistics and information.
    """
    
    def setUp(self):
        """Create staff user and test data for dashboard testing."""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        # Create various pets with different statuses for statistics
        Pet.objects.create(
            name="Available Pet 1",
            slug="available-1",
            type="dog",
            breed="Mix",
            age="2 years",
            gender="Male",
            size="Medium",
            color="Brown",
            description="Test",
            personality=["Friendly"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("100.00")
        )
        
        Pet.objects.create(
            name="Available Pet 2",
            slug="available-2",
            type="cat",
            breed="Mix",
            age="1 year",
            gender="Female",
            size="Small",
            color="White",
            description="Test",
            personality=["Playful"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("80.00")
        )
        
        Pet.objects.create(
            name="Adopted Pet",
            slug="adopted-1",
            type="dog",
            breed="Mix",
            age="3 years",
            gender="Male",
            size="Large",
            color="Black",
            description="Test",
            personality=["Calm"],
            status="adopted",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("120.00")
        )
    
    def test_dashboard_shows_correct_statistics(self):
        """
        Test that dashboard displays accurate statistics.
        
        The dashboard shows key metrics like number of available pets,
        pending applications, etc. These numbers must be accurate for
        staff to make informed decisions.
        
        Note: Based on your admin_views.py, the stats dictionary has
        these keys: pending_applications, available_pets, total_adopted, unread_messages
        """
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('admin_dashboard'))
        
        stats = response.context['stats']
        
        # We created 2 available pets and 1 adopted
        self.assertEqual(stats['available_pets'], 2)
        self.assertEqual(stats['total_adopted'], 1)
        
        # These should exist in the stats dictionary
        self.assertIn('pending_applications', stats)
        self.assertIn('unread_messages', stats)
    
    def test_dashboard_shows_recent_applications(self):
        """
        Test that dashboard shows recent adoption applications.
        
        Staff need to see recent applications to prioritize their work.
        The dashboard should show the most recent ones first.
        """
        # Create some applications
        user = User.objects.create_user(username='applicant', password='pass123')
        pet = Pet.objects.first()
        
        app1 = AdoptionApplication.objects.create(
            user=user,
            first_name='First',
            last_name='Applicant',
            email='first@example.com',
            phone='555-0001',
            address='Address 1',
            pet=pet,
            housing_type='house',
            own_or_rent='own',
            household_adults=2,
            previous_pet_experience='Experience',
            reason_for_adoption='Reason',
            status='pending',
            submitted_at=timezone.now() - timezone.timedelta(days=2)
        )
        
        app2 = AdoptionApplication.objects.create(
            user=user,
            first_name='Second',
            last_name='Applicant',
            email='second@example.com',
            phone='555-0002',
            address='Address 2',
            pet=pet,
            housing_type='apartment',
            own_or_rent='rent',
            household_adults=1,
            previous_pet_experience='Experience',
            reason_for_adoption='Reason',
            status='pending',
            submitted_at=timezone.now()  # Most recent
        )
        
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('admin_dashboard'))
        
        recent_apps = response.context['recent_applications']
        
        # Should show recent applications
        self.assertGreater(len(recent_apps), 0)
        
        # Most recent should be first (app2)
        self.assertEqual(recent_apps[0], app2)


class AdminApplicationManagementTests(TestCase):
    """
    Tests for adoption application management functionality.
    
    Staff need to review applications, update statuses, and add notes.
    These tests verify that these critical operations work correctly.
    """
    
    def setUp(self):
        """Create staff user, regular user, pet, and application for testing."""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        self.regular_user = User.objects.create_user(
            username='applicant',
            email='applicant@example.com',
            password='pass123',
            first_name='John',
            last_name='Doe'
        )
        
        self.pet = Pet.objects.create(
            name="Test Pet",
            slug="test-pet",
            type="dog",
            breed="Mix",
            age="2 years",
            gender="Male",
            size="Medium",
            color="Brown",
            description="Test pet",
            personality=["Friendly"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("150.00")
        )
        
        self.application = AdoptionApplication.objects.create(
            user=self.regular_user,
            first_name='John',
            last_name='Doe',
            email='applicant@example.com',
            phone='555-1234',
            address='123 Test St',
            pet=self.pet,
            housing_type='house',
            own_or_rent='own',
            household_adults=2,
            previous_pet_experience='Had dogs before',
            reason_for_adoption='Looking for companion',
            status='pending'
        )
    
    def test_admin_can_view_application_details(self):
        """
        Test that staff can view detailed application information.
        
        Staff need to see all details of an application to make
        informed decisions about approval.
        
        Note: Your URL uses 'application_id' parameter, not 'pk'
        """
        self.client.login(username='staffuser', password='staffpass123')
        
        url = reverse('admin_application_detail', kwargs={'application_id': self.application.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/admin/admin_application_detail.html')
        
        # Verify application is in context
        self.assertEqual(response.context['application'], self.application)
    
    def test_admin_can_update_application_status(self):
        """
        Test that staff can change application status.
        
        Critical functionality: Staff approve or reject applications.
        This test verifies the status update mechanism works correctly.
        
        Note: Your view expects 'status' in POST data, not a different field name
        """
        self.client.login(username='staffuser', password='staffpass123')
        
        # Update status to approved
        url = reverse('admin_update_application_status', kwargs={'application_id': self.application.pk})
        response = self.client.post(url, {'status': 'approved'})
        
        # Should redirect back (your view redirects to referring page or applications list)
        self.assertEqual(response.status_code, 302)
        
        # Refresh application from database
        self.application.refresh_from_db()
        
        # Verify status was updated
        self.assertEqual(self.application.status, 'approved')
    
    def test_completing_application_updates_pet_status(self):
        """
        Test that completing an application marks the pet as adopted.
        
        Business rule: When an application is marked as 'completed', the pet
        should be marked as "adopted". This is critical workflow logic.
        
        Note: Your view uses 'completed' status to mark pets as adopted,
        not 'approved' status. This is actually a better workflow!
        """
        self.client.login(username='staffuser', password='staffpass123')
        
        # Initially, pet is available
        self.assertEqual(self.pet.status, 'available')
        
        # Complete the application (this should adopt the pet)
        url = reverse('admin_update_application_status', kwargs={'application_id': self.application.pk})
        self.client.post(url, {'status': 'completed'})
        
        # Refresh pet from database
        self.pet.refresh_from_db()
        
        # Pet should now be adopted
        self.assertEqual(self.pet.status, 'adopted')
    
    def test_rejecting_application_keeps_pet_available(self):
        """
        Test that rejecting an application keeps pet available.
        
        Business rule: Rejected applications shouldn't affect pet
        availability - the pet should remain available for other adopters.
        """
        self.client.login(username='staffuser', password='staffpass123')
        
        # Reject the application
        url = reverse('admin_update_application_status', kwargs={'application_id': self.application.pk})
        self.client.post(url, {'status': 'rejected'})
        
        # Refresh pet from database
        self.pet.refresh_from_db()
        
        # Pet should still be available
        self.assertEqual(self.pet.status, 'available')
    
    def test_admin_can_add_notes_to_application(self):
        """
        Test that staff can add internal notes to applications.
        
        Staff need to record observations, interview notes, or reasons
        for decisions. This functionality supports better communication
        between staff members.
        
        Note: Your view expects field name 'notes', not 'admin_notes'
        """
        self.client.login(username='staffuser', password='staffpass123')
        
        notes = "Applicant seems very responsible. Called references - all positive."
        
        url = reverse('admin_update_application_notes', kwargs={'application_id': self.application.pk})
        response = self.client.post(url, {'notes': notes})
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Refresh application
        self.application.refresh_from_db()
        
        # Verify notes were saved
        self.assertEqual(self.application.notes, notes)
    
    def test_applications_list_shows_all_applications(self):
        """
        Test that applications list page shows all applications.
        
        Staff need to see all applications to manage workload and
        prioritize reviews.
        
        Note: Your view uses pagination, so applications in context
        is a Page object, not a QuerySet. We need to use len() instead of .count()
        """
        # Create another application
        AdoptionApplication.objects.create(
            user=self.regular_user,
            first_name='Second',
            last_name='Application',
            email='second@example.com',
            phone='555-5678',
            address='456 Other St',
            pet=self.pet,
            housing_type='apartment',
            own_or_rent='rent',
            household_adults=1,
            previous_pet_experience='First pet',
            reason_for_adoption='Want a companion',
            status='pending'
        )
        
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('admin_applications'))
        
        applications = response.context['applications']
        
        # Should show both applications
        # Your view returns a Page object, so we use len() instead of .count()
        self.assertEqual(len(applications), 2)
    
    def test_applications_list_can_filter_by_status(self):
        """
        Test that staff can filter applications by status.
        
        When there are many applications, filtering by status (pending,
        approved, rejected) helps staff focus on what needs attention.
        """
        # Create applications with different statuses
        AdoptionApplication.objects.create(
            user=self.regular_user,
            first_name='Approved',
            last_name='App',
            email='approved@example.com',
            phone='555-1111',
            address='Address',
            pet=self.pet,
            housing_type='house',
            own_or_rent='own',
            household_adults=2,
            previous_pet_experience='Experience',
            reason_for_adoption='Reason',
            status='approved'
        )
        
        self.client.login(username='staffuser', password='staffpass123')
        
        # Filter for pending only
        response = self.client.get(reverse('admin_applications'), {'status': 'pending'})
        applications = response.context['applications']
        
        # Should only show pending applications (1 in our case)
        self.assertEqual(len(applications), 1)
        self.assertEqual(applications[0].status, 'pending')


class AdminContactManagementTests(TestCase):
    """
    Tests for contact message management functionality.
    
    Staff need to review and respond to contact messages from visitors.
    These tests verify message management works correctly.
    """
    
    def setUp(self):
        """Create staff user and contact messages for testing."""
        self.client = Client()
        
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        
        self.message = ContactMessage.objects.create(
            name='Test Person',
            email='test@example.com',
            phone='555-1234',
            subject='Question about adoption',
            message='I have some questions about the adoption process.',
            is_read=False,
            is_responded=False
        )
    
    def test_admin_can_view_contact_messages(self):
        """
        Test that staff can view list of contact messages.
        
        Note: Your template is named 'admin_contacts.html', not 'contacts.html'
        """
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('admin_contacts'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'shelter/admin/admin_contacts.html')
        
        # Your view returns paginated results, so contacts is a Page object
        contacts = response.context['contacts']
        self.assertIn(self.message, contacts)
    
    def test_admin_can_view_contact_message_detail(self):
        """
        Test that staff can view individual message details.
        
        Note: Your URL uses 'contact_id' parameter, not 'pk'
        """
        self.client.login(username='staffuser', password='staffpass123')
        
        url = reverse('admin_contact_detail', kwargs={'contact_id': self.message.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['contact'], self.message)
    
    def test_viewing_message_marks_as_read(self):
        """
        Test that viewing a message automatically marks it as read.
        
        Business logic: When staff opens a message, it should be
        automatically marked as read to track which messages still
        need attention.
        """
        self.client.login(username='staffuser', password='staffpass123')
        
        # Message starts unread
        self.assertFalse(self.message.is_read)
        
        # View the message
        url = reverse('admin_contact_detail', kwargs={'contact_id': self.message.pk})
        self.client.get(url)
        
        # Refresh from database
        self.message.refresh_from_db()
        
        # Should now be marked as read
        self.assertTrue(self.message.is_read)
    
    def test_admin_can_mark_message_as_responded(self):
        """
        Test that staff can mark messages as responded to.
        
        After responding to a message via email or phone, staff should
        be able to mark it as responded in the system for tracking.
        
        Note: Your view expects POST data with action='mark_responded'
        """
        self.client.login(username='staffuser', password='staffpass123')
        
        url = reverse('admin_update_contact_status', kwargs={'contact_id': self.message.pk})
        response = self.client.post(url, {'action': 'mark_responded'})
        
        # Should redirect
        self.assertEqual(response.status_code, 302)
        
        # Refresh message
        self.message.refresh_from_db()
        
        # Should be marked as responded
        self.assertTrue(self.message.is_responded)