"""
Form Tests for PawHaven Shelter Application

Forms are the gatekeepers of data quality in your application. They validate
user input before it reaches your database. These tests verify that forms
accept valid data and reject invalid data with appropriate error messages.

Good form validation is critical - it prevents bad data from entering your
system while providing helpful feedback to users about what they need to fix.
"""

from django.test import TestCase
from django.contrib.auth.models import User

from shelter.forms import CustomUserCreationForm, UserUpdateForm


class CustomUserCreationFormTests(TestCase):
    """
    Tests for the user registration form.
    
    Registration is the first interaction many users have with your system.
    The form must validate usernames, emails, and passwords correctly while
    providing clear error messages when validation fails.
    """
    
    def test_valid_registration_form(self):
        """
        Test that form accepts valid registration data.
        
        This is the "happy path" - when a user provides all correct information,
        the form should validate successfully and be ready to save.
        """
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',  # Must match password1
        }
        
        form = CustomUserCreationForm(data=form_data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Should not have any errors
        self.assertEqual(len(form.errors), 0)
    
    def test_registration_form_password_mismatch(self):
        """
        Test that form rejects mismatched passwords.
        
        Security requirement: Users must type their password twice to confirm
        they didn't make a typo. If the passwords don't match, form should
        fail validation with a clear error message.
        """
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',  # Doesn't match!
        }
        
        form = CustomUserCreationForm(data=form_data)
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        
        # Should have error on password2 field
        self.assertIn('password2', form.errors)
    
    def test_registration_form_duplicate_username(self):
        """
        Test that form rejects duplicate usernames.
        
        Business rule: Usernames must be unique across the system.
        If someone tries to register with an existing username,
        the form should reject it with a helpful error message.
        """
        # Create an existing user
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        # Try to register with the same username
        form_data = {
            'username': 'existinguser',  # This username already exists!
            'email': 'different@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        
        form = CustomUserCreationForm(data=form_data)
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        
        # Should have error on username field
        self.assertIn('username', form.errors)
    
    def test_registration_form_invalid_email(self):
        """
        Test that form rejects invalid email addresses.
        
        Data quality test: Email addresses must be in valid format.
        Invalid formats should be caught before attempting to save.
        """
        form_data = {
            'username': 'newuser',
            'email': 'not-a-valid-email',  # Missing @ and domain
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        
        form = CustomUserCreationForm(data=form_data)
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        
        # Should have error on email field
        self.assertIn('email', form.errors)
    
    def test_registration_form_required_fields(self):
        """
        Test that form requires all necessary fields.
        
        Username, email, and password are mandatory. The form should enforce this.
        First name and last name are optional in your form.
        """
        # Submit form with missing required fields
        form_data = {
            'username': '',  # Empty username
            'email': '',     # Empty email
            'password1': '', # Empty password
            'password2': '',
        }
        
        form = CustomUserCreationForm(data=form_data)
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        
        # Should have errors for required fields
        self.assertIn('username', form.errors)
        self.assertIn('email', form.errors)
        self.assertIn('password1', form.errors)
    
    def test_registration_form_saves_user_correctly(self):
        """
        Test that valid form creates a User object correctly.
        
        Integration test: Beyond validation, the form must actually
        save the user to the database with all the correct information.
        """
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
        }
        
        form = CustomUserCreationForm(data=form_data)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
        
        # Save the form (creates the user)
        user = form.save()
        
        # Verify user was created with correct data
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        
        # Verify password was hashed (not stored in plain text)
        self.assertNotEqual(user.password, 'SecurePass123!')
        
        # Verify we can authenticate with the password
        self.assertTrue(user.check_password('SecurePass123!'))


class UserUpdateFormTests(TestCase):
    """
    Tests for the profile editing form.
    
    Users need to be able to update their profile information.
    This form is simpler than registration (no password handling),
    but still needs validation, especially for duplicate emails.
    """
    
    def setUp(self):
        """Create a user for profile update testing."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='password123'
        )
    
    def test_valid_profile_update(self):
        """
        Test that form accepts valid profile updates.
        """
        form_data = {
            'username': 'testuser',  # Keep same username
            'email': 'newemail@example.com',  # New email
            'first_name': 'Updated',  # New first name
            'last_name': 'Name',  # New last name
        }
        
        # Pass the existing user instance to the form
        form = UserUpdateForm(data=form_data, instance=self.user)
        
        # Form should be valid
        self.assertTrue(form.is_valid())
    
    def test_profile_update_saves_changes(self):
        """
        Test that valid form actually updates the user object.
        """
        form_data = {
            'username': 'testuser',
            'email': 'newemail@example.com',
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        
        self.assertTrue(form.is_valid())
        
        # Save the changes
        updated_user = form.save()
        
        # Verify changes were applied
        self.assertEqual(updated_user.email, 'newemail@example.com')
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
    
    def test_profile_update_invalid_email(self):
        """
        Test that form rejects invalid email addresses.
        """
        form_data = {
            'username': 'testuser',
            'email': 'invalid-email-format',
            'first_name': 'Test',
            'last_name': 'User',
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        
        # Should have error on email field
        self.assertIn('email', form.errors)
    
    def test_profile_update_duplicate_email(self):
        """
        Test that form rejects email addresses already in use by other users.
        
        Your UserUpdateForm has custom validation to prevent duplicate emails.
        This is important for preventing email conflicts in the system.
        """
        # Create another user with a different email
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        
        # Try to update our user's email to the other user's email
        form_data = {
            'username': 'testuser',
            'email': 'other@example.com',  # This email belongs to another user!
            'first_name': 'Test',
            'last_name': 'User',
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        
        # Form should be invalid
        self.assertFalse(form.is_valid())
        
        # Should have error on email field
        self.assertIn('email', form.errors)
        
        # Verify error message mentions the email is in use
        error_message = str(form.errors['email'])
        self.assertIn('already in use', error_message.lower())
    
    def test_profile_update_keep_same_email(self):
        """
        Test that user can keep their own email when updating profile.
        
        The duplicate email validation should allow users to keep their
        own email address even though it technically "exists" in the system.
        """
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',  # Same email as before
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        
        form = UserUpdateForm(data=form_data, instance=self.user)
        
        # Form should be valid - user can keep their own email
        self.assertTrue(form.is_valid())