import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from accounts.models import Brand

User = get_user_model()


@pytest.mark.django_db
class TestUserAuthentication:
    """Test user authentication flow."""

    def setup_method(self):
        """Set up test data."""
        self.client = APIClient()
        self.brand = Brand.objects.create(name="Test Brand")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            role="BRAND_MANAGER",
            brand=self.brand
        )

    def test_login_success(self):
        """Test successful login."""
        url = reverse('accounts:login')
        data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data)
        
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'user' in response.data
        assert response.data['user']['email'] == 'test@example.com'
        assert response.data['user']['role'] == 'BRAND_MANAGER'
        assert response.data['user']['brand_id'] == self.brand.id
        
        # Check if refresh cookie is set
        assert 'refresh_token' in response.cookies

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        url = reverse('accounts:login')
        data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)
        
        assert response.status_code == 401
        assert response.data['detail'] == 'Geçersiz giriş.'

    def test_login_missing_fields(self):
        """Test login with missing fields."""
        url = reverse('accounts:login')
        data = {'email': 'test@example.com'}
        response = self.client.post(url, data)
        
        assert response.status_code == 400

    def test_refresh_token_flow(self):
        """Test refresh token flow."""
        # First login to get tokens
        login_url = reverse('accounts:login')
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        login_response = self.client.post(login_url, login_data)
        
        # Extract refresh token from cookie
        refresh_token = login_response.cookies['refresh_token'].value
        
        # Use refresh token to get new access token
        refresh_url = reverse('accounts:refresh')
        self.client.cookies['refresh_token'] = refresh_token
        refresh_response = self.client.post(refresh_url)
        
        assert refresh_response.status_code == 200
        assert 'access' in refresh_response.data

    def test_refresh_token_missing(self):
        """Test refresh with missing token."""
        url = reverse('accounts:refresh')
        response = self.client.post(url)
        
        assert response.status_code == 401
        assert response.data['detail'] == 'Refresh yok.'

    def test_logout(self):
        """Test logout functionality."""
        # First login
        login_url = reverse('accounts:login')
        login_data = {
            'email': 'test@example.com',
            'password': 'testpassword123'
        }
        login_response = self.client.post(login_url, login_data)
        
        # Set the refresh token cookie
        refresh_token = login_response.cookies['refresh_token'].value
        self.client.cookies['refresh_token'] = refresh_token
        
        # Logout
        logout_url = reverse('accounts:logout')
        logout_response = self.client.post(logout_url)
        
        assert logout_response.status_code == 200
        assert logout_response.data['detail'] == 'Çıkış yapıldı.'