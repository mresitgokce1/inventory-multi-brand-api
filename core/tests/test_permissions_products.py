"""
Tests for permissions and brand-scoped access control.
"""
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Brand
from core.constants import ROLE_ADMIN, ROLE_BRAND_MANAGER
from core.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
class TestPermissionsAndBrandScoping:
    """
    Test permissions and brand-scoped access control.
    """

    def setup_method(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand 1")
        self.brand2 = Brand.objects.create(name="Brand 2")
        
        # Create users
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            role=ROLE_ADMIN
        )
        
        self.brand1_manager = User.objects.create_user(
            email="brand1@example.com",
            password="testpass123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand1
        )
        
        self.brand2_manager = User.objects.create_user(
            email="brand2@example.com",
            password="testpass123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand2
        )
        
        # Create categories
        self.category1 = Category.objects.create(
            brand=self.brand1,
            name="Brand 1 Category"
        )
        
        self.category2 = Category.objects.create(
            brand=self.brand2,
            name="Brand 2 Category"
        )
        
        # Create products
        self.product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Brand 1 Product",
            sku="B1P001",
            price=Decimal('10.00')
        )
        
        self.product2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Brand 2 Product",
            sku="B2P001",
            price=Decimal('20.00')
        )
        
        self.client = APIClient()

    def test_admin_sees_all_products(self):
        """Test that admin can see all products."""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get('/api/products/')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 2
        
        # Should contain both products
        product_ids = [p['id'] for p in results]
        assert self.product1.id in product_ids
        assert self.product2.id in product_ids

    def test_brand_manager_sees_only_own_brand_products(self):
        """Test that brand manager sees only their brand's products."""
        self.client.force_authenticate(user=self.brand1_manager)
        
        response = self.client.get('/api/products/')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product1.id

    def test_brand_manager_cannot_access_other_brand_product(self):
        """Test that brand manager cannot access other brand's product detail."""
        self.client.force_authenticate(user=self.brand1_manager)
        
        response = self.client.get(f'/api/products/{self.product2.id}/')
        
        # Should return 404 for security (obscurity)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_admin_can_access_any_product(self):
        """Test that admin can access any product detail."""
        self.client.force_authenticate(user=self.admin)
        
        response = self.client.get(f'/api/products/{self.product1.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.product1.id
        
        response = self.client.get(f'/api/products/{self.product2.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == self.product2.id

    def test_brand_manager_create_product_auto_sets_brand(self):
        """Test that brand manager's created product gets their brand automatically."""
        self.client.force_authenticate(user=self.brand1_manager)
        
        data = {
            'name': 'New Product',
            'sku': 'NEW001',
            'price': '15.00',
            'category': self.category1.id,
            # Note: not providing brand - should be auto-set
        }
        
        response = self.client.post('/api/products/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['brand'] == self.brand1.id
        
        # Verify in database
        product = Product.objects.get(id=response.data['id'])
        assert product.brand == self.brand1

    def test_brand_manager_cannot_create_for_other_brand(self):
        """Test that brand manager cannot create product for another brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        
        data = {
            'name': 'New Product',
            'sku': 'NEW001',
            'price': '15.00',
            'brand': self.brand2.id,  # Trying to set different brand
            'category': self.category1.id,
        }
        
        response = self.client.post('/api/products/', data)
        
        # Should succeed but brand should be auto-set to brand manager's brand
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['brand'] == self.brand1.id  # Should be auto-set

    def test_admin_must_provide_brand_on_create(self):
        """Test that admin must explicitly provide brand when creating."""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'name': 'New Product',
            'sku': 'NEW001',
            'price': '15.00',
            # Note: not providing brand
        }
        
        response = self.client.post('/api/products/', data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'brand' in response.data

    def test_admin_can_create_for_any_brand(self):
        """Test that admin can create product for any brand."""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'name': 'New Product',
            'sku': 'NEW001',
            'price': '15.00',
            'brand': self.brand2.id,
        }
        
        response = self.client.post('/api/products/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['brand'] == self.brand2.id

    def test_categories_same_brand_scoping(self):
        """Test that categories follow same brand scoping rules."""
        # Brand manager sees only their categories
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.get('/api/categories/')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.category1.id
        
        # Admin sees all categories
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/categories/')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 2

    def test_unauthenticated_user_cannot_access_private_endpoints(self):
        """Test that unauthenticated users cannot access private endpoints."""
        # No authentication
        response = self.client.get('/api/products/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        response = self.client.get('/api/categories/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_public_endpoint_allows_unauthenticated_access(self):
        """Test that public products endpoint allows unauthenticated access."""
        # No authentication needed
        response = self.client.get('/api/public/products/')
        
        assert response.status_code == status.HTTP_200_OK
        # Should show active products from all brands
        results = response.data['results']
        assert len(results) == 2

    def test_brand_manager_cannot_modify_other_brand_product(self):
        """Test that brand manager cannot modify other brand's product."""
        self.client.force_authenticate(user=self.brand1_manager)
        
        data = {
            'name': 'Modified Name',
            'price': '99.00'
        }
        
        response = self.client.patch(f'/api/products/{self.product2.id}/', data)
        
        # Should return 404 for security
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_brand_manager_can_modify_own_brand_product(self):
        """Test that brand manager can modify their own brand's product."""
        self.client.force_authenticate(user=self.brand1_manager)
        
        data = {
            'name': 'Modified Name',
            'price': '99.00'
        }
        
        response = self.client.patch(f'/api/products/{self.product1.id}/', data)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Modified Name'
        assert response.data['price'] == '99.00'