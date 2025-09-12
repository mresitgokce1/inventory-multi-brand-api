"""
Tests for QR Code functionality.
"""
import json
import base64
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Brand
from catalog.models import Product, Category, ProductQRCode
from catalog.utils import generate_base62_code, generate_unique_qr_code
from core.constants import ROLE_ADMIN, ROLE_BRAND_MANAGER

User = get_user_model()


class TestBase62Utils(TestCase):
    """Test Base62 code generation utilities."""
    
    def test_generate_base62_code_default_length(self):
        """Test Base62 code generation with default length."""
        code = generate_base62_code()
        self.assertEqual(len(code), 8)
        # Check all characters are valid Base62
        valid_chars = set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
        self.assertTrue(all(c in valid_chars for c in code))
    
    def test_generate_base62_code_custom_length(self):
        """Test Base62 code generation with custom length."""
        code = generate_base62_code(10)
        self.assertEqual(len(code), 10)
    
    def test_generate_unique_qr_code_uniqueness(self):
        """Test that generate_unique_qr_code produces unique codes."""
        # Create a brand and product first
        brand = Brand.objects.create(name="Test Brand")
        product = Product.objects.create(
            brand=brand,
            name="Test Product",
            sku="TEST001",
            price="99.99",
            stock=10
        )
        
        # Generate first code
        code1 = generate_unique_qr_code()
        ProductQRCode.objects.create(product=product, code=code1)
        
        # Generate second code - should be different
        code2 = generate_unique_qr_code()
        self.assertNotEqual(code1, code2)
    
    def test_generate_unique_qr_code_collision_handling(self):
        """Test that generate_unique_qr_code handles collisions."""
        # Create a brand and product
        brand = Brand.objects.create(name="Test Brand")
        product = Product.objects.create(
            brand=brand,
            name="Test Product",
            sku="TEST001",
            price="99.99",
            stock=10
        )
        
        # Mock generate_base62_code to return same value first two times
        with patch('catalog.utils.generate_base62_code') as mock_gen:
            mock_gen.side_effect = ['COLLISION', 'COLLISION', 'UNIQUE123']
            
            # Create first QR code with collision code
            ProductQRCode.objects.create(product=product, code='COLLISION')
            
            # Generate new code - should avoid collision
            unique_code = generate_unique_qr_code()
            self.assertEqual(unique_code, 'UNIQUE123')


class QRCodeModelTests(TestCase):
    """Test ProductQRCode model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.brand = Brand.objects.create(name="Test Brand")
        self.product = Product.objects.create(
            brand=self.brand,
            name="Test Product",
            sku="TEST001",
            price="99.99",
            stock=10
        )
    
    def test_qr_code_auto_generation(self):
        """Test that QR code is auto-generated when not provided."""
        qr_code = ProductQRCode.objects.create(product=self.product)
        self.assertIsNotNone(qr_code.code)
        self.assertTrue(len(qr_code.code) >= 8)
        self.assertTrue(qr_code.active)
    
    def test_qr_code_manual_code(self):
        """Test creating QR code with manual code."""
        manual_code = 'MANUAL123'
        qr_code = ProductQRCode.objects.create(product=self.product, code=manual_code)
        self.assertEqual(qr_code.code, manual_code)
    
    def test_qr_code_str_representation(self):
        """Test QR code string representation."""
        qr_code = ProductQRCode.objects.create(product=self.product, code='TEST1234')
        expected = f"QR Code TEST1234 for {self.product.name}"
        self.assertEqual(str(qr_code), expected)
    
    def test_qr_code_unique_constraint(self):
        """Test that QR codes must be unique."""
        code = 'UNIQUE123'
        ProductQRCode.objects.create(product=self.product, code=code)
        
        # Create another product
        product2 = Product.objects.create(
            brand=self.brand,
            name="Test Product 2",
            sku="TEST002",
            price="149.99",
            stock=5
        )
        
        # Try to create QR with same code - should fail
        with self.assertRaises(Exception):
            ProductQRCode.objects.create(product=product2, code=code)


class QRCodeAPITests(APITestCase):
    """Test QR Code API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand 1")
        self.brand2 = Brand.objects.create(name="Brand 2")
        
        # Create categories
        self.category1 = Category.objects.create(brand=self.brand1, name="Category 1")
        self.category2 = Category.objects.create(brand=self.brand2, name="Category 2")
        
        # Create products
        self.product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Product 1",
            sku="PROD001",
            price="99.99",
            stock=10,
            description="Test product 1"
        )
        self.product2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Product 2",
            sku="PROD002",
            price="149.99",
            stock=5,
            description="Test product 2"
        )
        
        # Create users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=ROLE_ADMIN
        )
        
        self.brand1_manager = User.objects.create_user(
            email='manager1@test.com',
            password='testpass123',
            role=ROLE_BRAND_MANAGER,
            brand=self.brand1
        )
        
        self.brand2_manager = User.objects.create_user(
            email='manager2@test.com',
            password='testpass123',
            role=ROLE_BRAND_MANAGER,
            brand=self.brand2
        )
        
        self.orphan_manager = User.objects.create_user(
            email='orphan@test.com',
            password='testpass123',
            role=ROLE_BRAND_MANAGER
            # No brand assigned
        )
    
    def get_jwt_token(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_qr_code_generation_as_admin(self):
        """Test QR code generation as admin user."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('catalog:product-qr-code', kwargs={'pk': self.product1.pk})
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('code', data)
        self.assertIn('url', data)
        self.assertIn('image_base64', data)
        self.assertEqual(data['mime_type'], 'image/png')
        
        # Check URL format
        expected_url = f"https://app.example.com/p/{data['code']}"
        self.assertEqual(data['url'], expected_url)
        
        # Check QR code was created in database
        qr_code = ProductQRCode.objects.get(product=self.product1)
        self.assertEqual(qr_code.code, data['code'])
        self.assertTrue(qr_code.active)
    
    def test_qr_code_generation_as_brand_manager(self):
        """Test QR code generation as brand manager for own product."""
        token = self.get_jwt_token(self.brand1_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('catalog:product-qr-code', kwargs={'pk': self.product1.pk})
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('code', data)
    
    def test_qr_code_generation_cross_brand_denied(self):
        """Test that brand manager cannot generate QR for other brand's product."""
        token = self.get_jwt_token(self.brand1_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('catalog:product-qr-code', kwargs={'pk': self.product2.pk})
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_qr_code_regeneration(self):
        """Test QR code regeneration functionality."""
        # First, create QR code
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('catalog:product-qr-code', kwargs={'pk': self.product1.pk})
        
        # Initial generation
        response1 = self.client.post(url, {})
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        data1 = response1.json()
        original_code = data1['code']
        
        # Get QR object and check regenerated_at is None
        qr_code = ProductQRCode.objects.get(product=self.product1)
        self.assertIsNone(qr_code.regenerated_at)
        
        # Regenerate
        response2 = self.client.post(url, {'regenerate': True})
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        data2 = response2.json()
        new_code = data2['code']
        
        # Codes should be different
        self.assertNotEqual(original_code, new_code)
        
        # Check regenerated_at is set
        qr_code.refresh_from_db()
        self.assertIsNotNone(qr_code.regenerated_at)
    
    def test_qr_code_custom_format_svg(self):
        """Test QR code generation in SVG format (currently falls back to PNG)."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('catalog:product-qr-code', kwargs={'pk': self.product1.pk})
        response = self.client.post(url, {'format': 'svg'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        # Currently falls back to PNG - TODO: implement proper SVG support
        self.assertEqual(data['mime_type'], 'image/png')
    
    def test_qr_code_custom_size(self):
        """Test QR code generation with custom size."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('catalog:product-qr-code', kwargs={'pk': self.product1.pk})
        response = self.client.post(url, {'size': 512})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_qr_code_unauthenticated_denied(self):
        """Test that unauthenticated users cannot generate QR codes."""
        url = reverse('catalog:product-qr-code', kwargs={'pk': self.product1.pk})
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class QRResolveAPITests(APITestCase):
    """Test QR Code resolve endpoint."""
    
    def setUp(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand 1")
        self.brand2 = Brand.objects.create(name="Brand 2")
        
        # Create categories
        self.category1 = Category.objects.create(brand=self.brand1, name="Category 1")
        
        # Create product
        self.product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Product 1",
            sku="PROD001",
            price="99.99",
            stock=10,
            description="Test product 1"
        )
        
        # Create QR code
        self.qr_code = ProductQRCode.objects.create(
            product=self.product1,
            code="TEST1234"
        )
        
        # Create users
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            role=ROLE_ADMIN
        )
        
        self.brand1_manager = User.objects.create_user(
            email='manager1@test.com',
            password='testpass123',
            role=ROLE_BRAND_MANAGER,
            brand=self.brand1
        )
        
        self.brand2_manager = User.objects.create_user(
            email='manager2@test.com',
            password='testpass123',
            role=ROLE_BRAND_MANAGER,
            brand=self.brand2
        )
    
    def get_jwt_token(self, user):
        """Get JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def test_qr_resolve_unauthenticated_public_fields(self):
        """Test QR resolve for unauthenticated user returns public fields only."""
        url = reverse('qr-resolve', kwargs={'code': self.qr_code.code})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['visibility'], 'public')
        
        # Check public fields
        public_data = data['product_public']
        self.assertEqual(public_data['id'], self.product1.id)
        self.assertEqual(public_data['name'], self.product1.name)
        self.assertEqual(public_data['slug'], self.product1.slug)
        self.assertEqual(public_data['price'], str(self.product1.price))
        self.assertEqual(public_data['description'], self.product1.description)
        
        # Check brand data
        self.assertEqual(public_data['brand']['id'], self.brand1.id)
        self.assertEqual(public_data['brand']['name'], self.brand1.name)
        
        # Check category data
        self.assertEqual(public_data['category']['id'], self.category1.id)
        self.assertEqual(public_data['category']['name'], self.category1.name)
        
        # Should not have private fields
        self.assertNotIn('product_private', data)
    
    def test_qr_resolve_admin_user_full_access(self):
        """Test QR resolve for admin user returns all fields."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('qr-resolve', kwargs={'code': self.qr_code.code})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['visibility'], 'admin')
        
        # Should have both public and private fields
        self.assertIn('product_public', data)
        self.assertIn('product_private', data)
        
        # Check private fields
        private_data = data['product_private']
        self.assertEqual(private_data['sku'], self.product1.sku)
        self.assertEqual(private_data['stock'], self.product1.stock)
    
    def test_qr_resolve_same_brand_manager_full_access(self):
        """Test QR resolve for same brand manager returns all fields."""
        token = self.get_jwt_token(self.brand1_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('qr-resolve', kwargs={'code': self.qr_code.code})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['visibility'], 'manager')
        
        # Should have both public and private fields
        self.assertIn('product_public', data)
        self.assertIn('product_private', data)
    
    def test_qr_resolve_different_brand_manager_public_only(self):
        """Test QR resolve for different brand manager returns public fields only."""
        token = self.get_jwt_token(self.brand2_manager)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('qr-resolve', kwargs={'code': self.qr_code.code})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['visibility'], 'public')
        self.assertIn('product_public', data)
        self.assertNotIn('product_private', data)
    
    def test_qr_resolve_invalid_code(self):
        """Test QR resolve with invalid code returns 404."""
        url = reverse('qr-resolve', kwargs={'code': 'INVALID123'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_qr_resolve_inactive_code(self):
        """Test QR resolve with inactive code returns 404."""
        # Make QR code inactive
        self.qr_code.active = False
        self.qr_code.save()
        
        url = reverse('qr-resolve', kwargs={'code': self.qr_code.code})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_qr_resolve_image_base64_validation(self):
        """Test that QR code generation returns valid base64 encoded image."""
        token = self.get_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        url = reverse('catalog:product-qr-code', kwargs={'pk': self.product1.pk})
        response = self.client.post(url, {})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Validate base64 decoding
        try:
            image_data = base64.b64decode(data['image_base64'])
            # Check PNG header
            self.assertTrue(image_data.startswith(b'\x89PNG'))
        except Exception as e:
            self.fail(f"Failed to decode base64 image: {e}")