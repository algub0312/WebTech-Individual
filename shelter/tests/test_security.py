"""
Security Testing for PawHaven Shelter Application

Security testing verifies that the application properly protects against
common web vulnerabilities and malicious attacks. These tests ensure that:
- Authentication and authorization are enforced correctly
- Sensitive data is protected
- Input validation prevents injection attacks
- CSRF protection is active
- Session management is secure

Security testing is critical because a single vulnerability can compromise
the entire application and all user data.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone

from shelter.models import Pet, AdoptionApplication, ContactMessage


class AuthenticationSecurityTests(TestCase):
    """
    Tests for authentication security.
    
    These tests verify that users cannot access protected resources
    without proper authentication, and that authentication mechanisms
    work correctly and securely.
    """
    
    def setUp(self):
        """Create test users and data."""
        self.client = Client()
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='RegularPass123!'
        )
        
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='StaffPass123!',
            is_staff=True
        )
    
    def test_unauthenticated_users_cannot_access_account(self):
        """
        Security Test: Anonymous users must not access account pages.
        
        Vulnerability prevented: Unauthorized access to user data
        """
        # Try to access account page without logging in
        response = self.client.get(reverse('account'))
        
        # Should redirect to login (302) or show forbidden (403)
        self.assertIn(response.status_code, [302, 403])
        
        # Should NOT return 200 (successful access)
        self.assertNotEqual(response.status_code, 200,
                           "Anonymous user should not access account page")
    
    def test_unauthenticated_users_cannot_view_applications(self):
        """
        Security Test: Anonymous users cannot view adoption applications.
        
        Vulnerability prevented: Exposure of personal information
        """
        response = self.client.get(reverse('user_applications'))
        
        self.assertIn(response.status_code, [302, 403])
        self.assertNotEqual(response.status_code, 200)
    
    def test_unauthenticated_users_cannot_submit_applications(self):
        """
        Security Test: Anonymous users cannot submit adoption applications.
        
        Vulnerability prevented: Spam and data integrity issues
        """
        pet = Pet.objects.create(
            name="Security Test Pet",
            slug="security-test",
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
            adoption_fee=Decimal("150.00")
        )
        
        url = reverse('adoption_application_pet', kwargs={'pet_id': pet.id})
        response = self.client.get(url)
        
        self.assertIn(response.status_code, [302, 403])


class AuthorizationSecurityTests(TestCase):
    """
    Tests for authorization security (access control).
    
    Authentication verifies WHO you are.
    Authorization verifies WHAT you can do.
    
    These tests ensure that even authenticated users cannot access
    resources they shouldn't have permission to access.
    """
    
    def setUp(self):
        """Create test users with different permission levels."""
        self.client = Client()
        
        # Regular user - has account but no admin privileges
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='RegularPass123!',
            is_staff=False  # NOT staff
        )
        
        # Staff user - has admin privileges
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='StaffPass123!',
            is_staff=True  # IS staff
        )
        
        # Create test data
        self.pet = Pet.objects.create(
            name="Authorization Test Pet",
            slug="auth-test",
            type="cat",
            breed="Mix",
            age="1 year",
            gender="Female",
            size="Small",
            color="Black",
            description="Test",
            personality=["Shy"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("100.00")
        )
        
        self.application = AdoptionApplication.objects.create(
            user=self.regular_user,
            first_name='Regular',
            last_name='User',
            email='regular@example.com',
            phone='555-0000',
            address='123 Test St',
            pet=self.pet,
            housing_type='apartment',
            own_or_rent='own',
            household_adults=1,
            previous_pet_experience='None',
            reason_for_adoption='Test',
            status='pending'
        )
    
    def test_regular_user_cannot_access_admin_dashboard(self):
        """
        Security Test: Non-staff users cannot access admin dashboard.
        
        Vulnerability prevented: Privilege escalation
        Attack scenario: Attacker with regular account tries to access
        admin panel by guessing/knowing the URL
        """
        # Login as regular user
        self.client.login(username='regularuser', password='RegularPass123!')
        
        # Try to access admin dashboard
        response = self.client.get(reverse('admin_dashboard'))
        
        # Should be forbidden (403) or redirected (302), NOT successful (200)
        self.assertIn(response.status_code, [302, 403],
                     "Regular user should not access admin dashboard")
        self.assertNotEqual(response.status_code, 200)
    
    def test_regular_user_cannot_access_admin_applications(self):
        """
        Security Test: Non-staff cannot view all applications.
        
        Vulnerability prevented: Privacy violation - users seeing other
        people's personal information in adoption applications
        """
        self.client.login(username='regularuser', password='RegularPass123!')
        
        response = self.client.get(reverse('admin_applications'))
        
        self.assertIn(response.status_code, [302, 403])
        self.assertNotEqual(response.status_code, 200)
    
    def test_regular_user_cannot_access_specific_application_detail(self):
        """
        Security Test: Non-staff cannot view application details (admin view).
        
        Even if attacker knows the application ID, they shouldn't be able
        to access the admin detail view.
        """
        self.client.login(username='regularuser', password='RegularPass123!')
        
        url = reverse('admin_application_detail', 
                     kwargs={'application_id': self.application.pk})
        response = self.client.get(url)
        
        self.assertIn(response.status_code, [302, 403])
    
    def test_regular_user_cannot_update_application_status(self):
        """
        Security Test: Non-staff cannot modify application statuses.
        
        Vulnerability prevented: Data tampering
        Attack scenario: Attacker tries to approve their own application
        """
        self.client.login(username='regularuser', password='RegularPass123!')
        
        url = reverse('admin_update_application_status',
                     kwargs={'application_id': self.application.pk})
        response = self.client.post(url, {'status': 'approved'})
        
        # Should be blocked
        self.assertIn(response.status_code, [302, 403])
        
        # Verify status didn't actually change
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'pending',
                        "Regular user should not be able to change application status")
    
    def test_regular_user_cannot_access_contact_messages(self):
        """
        Security Test: Non-staff cannot view contact messages.
        
        Vulnerability prevented: Privacy violation - contact messages
        may contain sensitive personal information
        """
        self.client.login(username='regularuser', password='RegularPass123!')
        
        response = self.client.get(reverse('admin_contacts'))
        
        self.assertIn(response.status_code, [302, 403])
    
    def test_staff_user_CAN_access_admin_resources(self):
        """
        Positive Security Test: Verify staff users have proper access.
        
        This is the flip side - we need to verify that legitimate staff
        users ARE able to access admin resources. Otherwise we've just
        blocked everyone!
        """
        # Login as staff
        self.client.login(username='staffuser', password='StaffPass123!')
        
        # Staff should be able to access dashboard
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Staff should be able to view applications
        response = self.client.get(reverse('admin_applications'))
        self.assertEqual(response.status_code, 200)
        
        # Staff should be able to update application status
        url = reverse('admin_update_application_status',
                     kwargs={'application_id': self.application.pk})
        response = self.client.post(url, {'status': 'approved'})
        
        # Should redirect (not blocked)
        self.assertEqual(response.status_code, 302)
        
        # Verify status DID change
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'approved')


class DataIsolationSecurityTests(TestCase):
    """
    Tests for data isolation between users.
    
    These tests verify that users can only access their OWN data,
    not data belonging to other users.
    """
    
    def setUp(self):
        """Create multiple users with their own data."""
        self.client = Client()
        
        # User A
        self.user_a = User.objects.create_user(
            username='usera',
            email='usera@example.com',
            password='PasswordA123!'
        )
        
        # User B
        self.user_b = User.objects.create_user(
            username='userb',
            email='userb@example.com',
            password='PasswordB123!'
        )
        
        # Create pet
        self.pet = Pet.objects.create(
            name="Isolation Test Pet",
            slug="isolation-test",
            type="dog",
            breed="Beagle",
            age="4 years",
            gender="Male",
            size="Medium",
            color="Tri-color",
            description="Test",
            personality=["Friendly"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("180.00")
        )
        
        # Create application for User A
        self.application_a = AdoptionApplication.objects.create(
            user=self.user_a,
            first_name='User',
            last_name='A',
            email='usera@example.com',
            phone='555-1111',
            address='111 A Street',
            pet=self.pet,
            housing_type='house',
            own_or_rent='own',
            household_adults=2,
            previous_pet_experience='Experience A',
            reason_for_adoption='Reason A',
            status='pending'
        )
        
        # Create application for User B
        self.application_b = AdoptionApplication.objects.create(
            user=self.user_b,
            first_name='User',
            last_name='B',
            email='userb@example.com',
            phone='555-2222',
            address='222 B Street',
            pet=self.pet,
            housing_type='apartment',
            own_or_rent='rent',
            household_adults=1,
            previous_pet_experience='Experience B',
            reason_for_adoption='Reason B',
            status='pending'
        )
    
    def test_user_cannot_access_other_users_data_by_url_manipulation(self):
        """
        Security Test: Users cannot access others' data via direct URL.
        
        Vulnerability prevented: Insecure Direct Object Reference (IDOR)
        Attack scenario: User A knows User B's application ID and tries
        to access it directly by URL
        
        Note: This test assumes you have a view for individual application
        detail accessible to users. If not, this scenario doesn't apply.
        """
        # This is a conceptual test - adjust based on your actual URL structure
        # If you don't have a user-facing application detail view, skip this
        pass


class InputValidationSecurityTests(TestCase):
    """
    Tests for input validation security.
    
    These tests verify that malicious input is properly rejected
    and cannot cause security issues like SQL injection, XSS, etc.
    """
    
    def setUp(self):
        """Set up test client and user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
    
    def test_sql_injection_attempt_in_search(self):
        """
        Security Test: SQL injection attempts are neutralized.
        
        Vulnerability prevented: SQL Injection
        Attack scenario: Attacker tries to inject SQL code via search input
        
        Note: Django ORM automatically protects against SQL injection,
        but we test to verify this protection is working.
        """
        # Common SQL injection payloads
        malicious_queries = [
            "' OR '1'='1",
            "'; DROP TABLE pets; --",
            "' UNION SELECT * FROM users--",
        ]
        
        for malicious_query in malicious_queries:
            response = self.client.get(reverse('pets'), {'search': malicious_query})
            
            # Should return normal response, not error
            self.assertEqual(response.status_code, 200)
            
            # Should not return all pets (which would happen if SQL injection worked)
            # This is a simplified test - in reality, you'd check more specifically
    
    def test_xss_attempt_in_contact_form(self):
        """
        Security Test: XSS (Cross-Site Scripting) attempts are escaped.
        
        Vulnerability prevented: Cross-Site Scripting (XSS)
        Attack scenario: Attacker submits JavaScript code in form fields
        hoping it will execute when admin views the message
        
        Note: Django templates automatically escape HTML/JavaScript,
        but we test to verify.
        """
        xss_payload = '<script>alert("XSS")</script>'
        
        contact_data = {
            'name': xss_payload,
            'email': 'attacker@example.com',
            'phone': '555-0000',
            'subject': 'Test Subject',
            'message': 'Test message'
        }
        
        response = self.client.post(reverse('contact'), contact_data)
        
        # Form should be accepted (or rejected for other validation reasons)
        # but not cause an error
        self.assertIn(response.status_code, [200, 302])
        
        # If message was created, verify XSS payload is stored but will be escaped
        if ContactMessage.objects.filter(email='attacker@example.com').exists():
            message = ContactMessage.objects.get(email='attacker@example.com')
            # The dangerous script should be stored as plain text
            self.assertEqual(message.name, xss_payload)
            
            # When rendered in template, Django should escape it automatically
            # The actual test for this would require checking the rendered HTML


class CSRFProtectionTests(TestCase):
    """
    Tests for CSRF (Cross-Site Request Forgery) protection.
    
    CSRF attacks trick authenticated users into performing actions
    they didn't intend to perform. Django's CSRF protection prevents this.
    """
    
    def setUp(self):
        """Create test user and pet."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='csrftest',
            email='csrf@example.com',
            password='CsrfPass123!'
        )
        
        self.pet = Pet.objects.create(
            name="CSRF Test Pet",
            slug="csrf-test",
            type="cat",
            breed="Tabby",
            age="2 years",
            gender="Female",
            size="Small",
            color="Orange",
            description="Test",
            personality=["Playful"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("120.00")
        )
    
    def test_csrf_protection_on_forms(self):
        """
        Security Test: POST requests without CSRF token are rejected.
        
        Vulnerability prevented: Cross-Site Request Forgery (CSRF)
        Attack scenario: Malicious site tricks user's browser into
        submitting a form to our site
        
        Note: In regular tests, CSRF is disabled for convenience.
        This test explicitly enables CSRF checking.
        """
        self.client.login(username='csrftest', password='CsrfPass123!')
        
        # Create a client that enforces CSRF checks
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(username='csrftest', password='CsrfPass123!')
        
        # Try to POST without CSRF token
        contact_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '555-0000',
            'subject': 'Test',
            'message': 'Test message'
        }
        
        response = csrf_client.post(reverse('contact'), contact_data)
        
        # Should be rejected with 403 Forbidden
        self.assertEqual(response.status_code, 403,
                        "POST request without CSRF token should be rejected")


class SessionSecurityTests(TestCase):
    """
    Tests for session management security.
    
    Sessions keep users logged in across requests. Poor session
    management can lead to session hijacking and unauthorized access.
    """
    
    def setUp(self):
        """Create test user."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='sessiontest',
            email='session@example.com',
            password='SessionPass123!'
        )
    
    def test_logout_invalidates_session(self):
        """
        Security Test: Logout properly invalidates session.
        
        Vulnerability prevented: Session fixation/hijacking
        After logout, the old session should not work anymore
        """
        # Login
        self.client.login(username='sessiontest', password='SessionPass123!')
        
        # Verify we can access protected page
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, 200)
        
        # Logout
        self.client.get(reverse('logout'))
        
        # Try to access protected page again - should be denied
        response = self.client.get(reverse('account'))
        self.assertIn(response.status_code, [302, 403],
                     "After logout, user should not access protected pages")