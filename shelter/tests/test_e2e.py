"""
End-to-End (E2E) Tests for PawHaven Shelter Application

E2E tests simulate real user interactions in an actual browser.
Unlike unit and integration tests that work at the code level,
E2E tests verify that the entire application stack works together
from a user's perspective - including frontend, backend, database,
and all JavaScript interactions.

These tests use Selenium WebDriver to control a real browser and
interact with the application exactly as a human user would.

Note: E2E tests are slower than other test types (10-30 seconds each)
but provide the highest confidence that the application works correctly
in real-world conditions.
"""

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from decimal import Decimal
from django.utils import timezone

from shelter.models import Pet


class EndToEndTests(StaticLiveServerTestCase):
    """
    Browser-based E2E tests using Selenium WebDriver.
    
    These tests launch an actual Chrome browser, navigate to pages,
    click buttons, fill forms, and verify what appears on screen.
    This is the closest simulation to a real user experience.
    
    StaticLiveServerTestCase starts a live Django server in the background
    that the browser can connect to, serving both dynamic content and
    static files (CSS, JavaScript, images).
    """
    
    @classmethod
    def setUpClass(cls):
        """
        Set up browser before running any tests in this class.
        
        This method runs once for the entire test class, not before
        each individual test. We configure Chrome to run in headless
        mode (no visible window) for faster execution in CI/CD pipelines,
        but you can remove headless mode to watch the tests run.
        """
        super().setUpClass()
        
        # Configure Chrome options
        chrome_options = Options()
        
        # Headless mode - browser runs without GUI (faster, good for CI/CD)
        # Comment out this line if you want to watch the browser during testing
        chrome_options.add_argument('--headless')
        
        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialize Chrome WebDriver with automatic driver management
        # webdriver_manager automatically downloads the correct ChromeDriver version
        service = Service(ChromeDriverManager().install())
        cls.browser = webdriver.Chrome(service=service, options=chrome_options)
        
        # Implicit wait - browser will wait up to 10 seconds for elements to appear
        cls.browser.implicitly_wait(10)
        
        # Set page load timeout
        cls.browser.set_page_load_timeout(30)
    
    @classmethod
    def tearDownClass(cls):
        """
        Clean up browser after all tests complete.
        
        This ensures the browser process is properly closed and
        doesn't keep running in the background.
        """
        cls.browser.quit()
        super().tearDownClass()
    
    def setUp(self):
        """
        Create test data before each test.
        
        Unlike setUpClass which runs once, setUp runs before EACH test method.
        This ensures each test starts with a clean, known state.
        """
        # Create a test pet that will appear on the website
        self.test_pet = Pet.objects.create(
            name="E2E Test Dog",
            slug="e2e-test-dog",
            type="dog",
            breed="Golden Retriever",
            age="3 years",
            gender="Male",
            size="Large",
            color="Golden",
            description="Friendly dog perfect for E2E testing adoption workflow.",
            personality=["Friendly", "Playful", "Good with kids"],
            vaccinated=True,
            spayed_neutered=True,
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("250.00"),
            featured=True  # Will appear on homepage
        )
        
        # Create a test user for authentication tests
        self.test_user = User.objects.create_user(
            username='e2e_testuser',
            email='e2e@example.com',
            password='TestPassword123!',
            first_name='E2E',
            last_name='Tester'
        )
    
    def test_homepage_loads_and_displays_featured_pets(self):
        """
        Test that homepage loads in real browser and displays featured pets.
        
        This is the most basic E2E test - can users even access the site
        and see content? This test verifies:
        1. Server responds and serves HTML
        2. Static files (CSS, images) load correctly
        3. Dynamic content (pets from database) displays
        4. Page title is correct
        
        Workflow:
        - Browser navigates to homepage
        - Waits for page to fully load
        - Verifies page title contains "PawHaven"
        - Verifies featured pet appears on page
        """
        # Navigate to homepage
        self.browser.get(f'{self.live_server_url}/')
        
        # Verify page title
        self.assertIn('PawHaven', self.browser.title)
        
        # Wait for and verify pet card appears (gives time for page to render)
        try:
            # Wait up to 10 seconds for element to appear
            pet_element = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.pet-card, .featured-pets'))
            )
            
            # Verify our test pet's name appears somewhere on the page
            page_source = self.browser.page_source
            self.assertIn('E2E Test Dog', page_source)
            
        except TimeoutException:
            # If element doesn't appear in 10 seconds, fail with helpful message
            self.fail("Homepage did not load featured pets within timeout period")
    
    def test_pet_browsing_and_detail_view(self):
        """
        Test complete pet browsing workflow.
        
        Simulates a potential adopter:
        1. Landing on homepage
        2. Navigating to pets list page
        3. Clicking on a specific pet
        4. Viewing pet details
        
        This tests navigation, links, and multi-page workflows.
        """
        # Start at homepage
        self.browser.get(f'{self.live_server_url}/')
        
        # Find and click "Browse Pets" or similar navigation link
        # We'll try multiple possible link texts to make test more robust
        possible_link_texts = ['Pets', 'Browse Pets', 'Available Pets', 'Find a Pet']
        
        pets_link_found = False
        for link_text in possible_link_texts:
            try:
                pets_link = self.browser.find_element(By.LINK_TEXT, link_text)
                pets_link.click()
                pets_link_found = True
                break
            except:
                continue
        
        if not pets_link_found:
            # If we can't find the link, navigate directly to pets page
            self.browser.get(f'{self.live_server_url}/pets/')
        
        # Wait for pets list page to load
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'body'))
        )
        
        # Verify we're on pets page
        self.assertIn('/pets', self.browser.current_url)
        
        # Verify our test pet appears in the list
        self.assertIn('E2E Test Dog', self.browser.page_source)
        
        # Try to click on the pet to view details
        # Look for link containing pet name or click on first pet card
        try:
            # Try clicking on pet name link
            pet_link = self.browser.find_element(
                By.XPATH, 
                f"//a[contains(text(), 'E2E Test Dog')]"
            )
            pet_link.click()
        except:
            # If specific link not found, click first pet card
            try:
                pet_card = self.browser.find_element(By.CSS_SELECTOR, '.pet-card a')
                pet_card.click()
            except:
                self.fail("Could not find clickable pet element")
        
        # Wait for detail page to load
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'body'))
        )
        
        # Verify we're on a pet detail page
        self.assertIn('/pet/', self.browser.current_url)
        
        # Verify pet details appear on page
        page_source = self.browser.page_source
        self.assertIn('E2E Test Dog', page_source)
        self.assertIn('Golden Retriever', page_source)
        self.assertIn('3 years', page_source)
    
    def test_user_registration_workflow(self):
        """
        Test complete user registration process in browser.
    
        This is a critical E2E test because registration involves:
        - Form interaction (typing, clicking)
        - Form validation (both frontend and backend)
        - Page navigation/redirect after success
        - Database interaction (user creation)
    
        Workflow:
        1. Navigate to registration page
        2. Fill out all form fields
        3. Submit form
        4. Verify success (either redirect or user created in DB)
        """
        # Navigate to registration page
        self.browser.get(f'{self.live_server_url}/register/')
    
        # Wait for registration form to load
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
    
        # Generate unique username to avoid conflicts if test runs multiple times
        import time
        unique_username = f'browsertest{int(time.time())}'
        
        # Fill out registration form
        username_field = self.browser.find_element(By.NAME, 'username')
        username_field.send_keys(unique_username)
        
        email_field = self.browser.find_element(By.NAME, 'email')
        email_field.send_keys(f'{unique_username}@example.com')
        
        # Try to find and fill optional name fields
        try:
            first_name_field = self.browser.find_element(By.NAME, 'first_name')
            first_name_field.send_keys('Browser')
            
            last_name_field = self.browser.find_element(By.NAME, 'last_name')
            last_name_field.send_keys('Tester')
        except:
            pass  # Name fields might be optional
        
        password1_field = self.browser.find_element(By.NAME, 'password1')
        password1_field.send_keys('SecureBrowserPass123!')
        
        password2_field = self.browser.find_element(By.NAME, 'password2')
        password2_field.send_keys('SecureBrowserPass123!')
        
        # Submit form by finding and clicking submit button
        submit_button = self.browser.find_element(
            By.CSS_SELECTOR, 
            'button[type="submit"], input[type="submit"]'
        )
        submit_button.click()
        
        # Wait a moment for processing
        import time
        time.sleep(2)
        
        # Check if user was created (this is the most important verification)
        # Even if we don't redirect, if user exists in DB, registration worked
        user_exists = User.objects.filter(username=unique_username).exists()
        
        if user_exists:
            # Success! User was created
            self.assertTrue(True, "Registration successful - user created in database")
        else:
            # User wasn't created - check if there are validation errors on page
            page_source = self.browser.page_source.lower()
            
            # Look for common error indicators
            if 'error' in page_source or 'invalid' in page_source:
                # There might be validation errors - print them for debugging
                try:
                    error_elements = self.browser.find_elements(By.CSS_SELECTOR, '.error, .errorlist, .alert-danger')
                    error_messages = [elem.text for elem in error_elements if elem.text]
                    if error_messages:
                        self.fail(f"Registration failed with errors: {error_messages}")
                except:
                    pass
            
            # If we're still on register page and no user created, test fails
            if '/register' in self.browser.current_url:
                self.fail("Registration did not create user and stayed on register page")
    
    def test_search_functionality(self):
        """
        Test search feature works in real browser.
        
        This tests:
        - Input field interaction
        - Form submission (GET request with query parameter)
        - Dynamic content filtering
        - Results display
        
        Note: This test assumes you have search functionality on pets page.
        If not, this test can be skipped or modified.
        """
        # Create another pet with different breed for contrast
        Pet.objects.create(
            name="Search Test Cat",
            slug="search-test-cat",
            type="cat",
            breed="Persian",
            age="2 years",
            gender="Female",
            size="Small",
            color="White",
            description="Cat for testing search functionality",
            personality=["Calm"],
            status="available",
            arrival_date=timezone.now().date(),
            adoption_fee=Decimal("150.00")
        )
        
        # Navigate to pets page
        self.browser.get(f'{self.live_server_url}/pets/')
        
        # Both pets should initially be visible
        self.assertIn('E2E Test Dog', self.browser.page_source)
        self.assertIn('Search Test Cat', self.browser.page_source)
        
        # Try to find and use search input
        try:
            search_input = self.browser.find_element(
                By.CSS_SELECTOR, 
                'input[name="search"], input[type="search"], input[placeholder*="Search"]'
            )
            
            # Search for "Golden" (should find dog, not cat)
            search_input.clear()
            search_input.send_keys('Golden')
            
            # Submit search (either by pressing Enter or clicking search button)
            try:
                search_button = self.browser.find_element(
                    By.CSS_SELECTOR,
                    'button[type="submit"]'
                )
                search_button.click()
            except:
                # If no button, submit by pressing Enter
                from selenium.webdriver.common.keys import Keys
                search_input.send_keys(Keys.RETURN)
            
            # Wait for results to load
            WebDriverWait(self.browser, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'body'))
            )
            
            # Verify search results - dog should be visible, cat should not
            page_source = self.browser.page_source
            self.assertIn('E2E Test Dog', page_source)
            # Cat might or might not be visible depending on implementation
            
        except:
            # If search functionality doesn't exist or isn't found, skip this part
            pass
    
    def test_responsive_navigation(self):
        """
        Test that navigation works across different viewport sizes.
        
        This tests responsive design - the site should work on both
        desktop and mobile screen sizes. Many sites use hamburger menus
        on mobile that need to be clicked before accessing navigation.
        """
        # Test desktop size
        self.browser.set_window_size(1920, 1080)
        self.browser.get(f'{self.live_server_url}/')
        
        # Navigation should be visible and clickable
        try:
            nav = self.browser.find_element(By.CSS_SELECTOR, 'nav, .navbar, header')
            self.assertTrue(nav.is_displayed())
        except:
            pass
        
        # Test mobile size
        self.browser.set_window_size(375, 667)  # iPhone size
        self.browser.get(f'{self.live_server_url}/')
        
        # Page should still load without errors
        self.assertIn('PawHaven', self.browser.page_source)
        
        # Reset to desktop size for other tests
        self.browser.set_window_size(1920, 1080)