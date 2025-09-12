"""
Tests for brand scoping permissions in catalog views.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Brand, User
from catalog.models import Category, Product
from core.constants import ROLE_ADMIN, ROLE_BRAND_MANAGER


class TestBrandScopingPermissions(TestCase):
    """Test brand scoping permissions for catalog endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create brands
        self.brand1 = Brand.objects.create(name="TechCorp", slug="techcorp")
        self.brand2 = Brand.objects.create(name="GadgetInc", slug="gadgetinc")
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="admin123",
            role=ROLE_ADMIN
        )
        
        # Create brand managers
        self.brand1_manager = User.objects.create_user(
            email="brand1@example.com",
            password="brand123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand1
        )
        
        self.brand2_manager = User.objects.create_user(
            email="brand2@example.com",
            password="brand123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand2
        )
        
        self.orphan_manager = User.objects.create_user(
            email="orphan@example.com",
            password="orphan123",
            role=ROLE_BRAND_MANAGER,
            brand=None  # No brand assigned
        )
        
        # Create categories for each brand
        self.category1 = Category.objects.create(
            brand=self.brand1,
            name="Laptops",
            slug="laptops"
        )
        
        self.category2 = Category.objects.create(
            brand=self.brand2,
            name="Tablets",
            slug="tablets"
        )
        
        # Create products for each brand
        self.product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99
        )
        
        self.product2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Pro Tablet",
            sku="TABLET-001",
            price=899.99
        )
    
    def test_admin_can_see_all_categories(self):
        """Test that admin users can see all categories across brands."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify both brand categories are present
        category_brands = {cat['brand'] for cat in response.data['results']}
        self.assertEqual(category_brands, {self.brand1.id, self.brand2.id})
    
    def test_brand_manager_sees_only_own_categories(self):
        """Test that brand managers only see their own brand's categories."""
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.get('/api/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['brand'], self.brand1.id)
    
    def test_orphan_brand_manager_sees_no_categories(self):
        """Test that brand manager without brand sees no categories."""
        self.client.force_authenticate(user=self.orphan_manager)
        response = self.client.get('/api/categories/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_admin_can_see_all_products(self):
        """Test that admin users can see all products across brands."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # Verify both brand products are present
        product_brands = {prod['brand'] for prod in response.data['results']}
        self.assertEqual(product_brands, {self.brand1.id, self.brand2.id})
    
    def test_brand_manager_sees_only_own_products(self):
        """Test that brand managers only see their own brand's products."""
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.get('/api/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['brand'], self.brand1.id)
    
    def test_orphan_brand_manager_sees_no_products(self):
        """Test that brand manager without brand sees no products."""
        self.client.force_authenticate(user=self.orphan_manager)
        response = self.client.get('/api/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 0)
    
    def test_brand_manager_cannot_access_other_brand_category(self):
        """Test that brand manager cannot access category from another brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.get(f'/api/categories/{self.category2.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_brand_manager_cannot_access_other_brand_product(self):
        """Test that brand manager cannot access product from another brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.get(f'/api/products/{self.product2.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_brand_manager_can_access_own_category(self):
        """Test that brand manager can access their own brand's category."""
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.get(f'/api/categories/{self.category1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['brand'], self.brand1.id)
    
    def test_brand_manager_can_access_own_product(self):
        """Test that brand manager can access their own brand's product."""
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.get(f'/api/products/{self.product1.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['brand'], self.brand1.id)
    
    def test_admin_can_create_category_for_any_brand(self):
        """Test that admin can create category for any brand."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'brand': self.brand2.id,
            'name': 'Admin Created Category',
            'is_active': True
        }
        response = self.client.post('/api/categories/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['brand'], self.brand2.id)
    
    def test_brand_manager_creates_category_for_own_brand(self):
        """Test that brand manager automatically creates category for their brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        data = {
            'name': 'Brand Manager Category',
            'is_active': True
        }
        response = self.client.post('/api/categories/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['brand'], self.brand1.id)
    
    def test_brand_manager_cannot_create_category_for_other_brand(self):
        """Test that brand manager cannot specify other brand when creating category."""
        self.client.force_authenticate(user=self.brand1_manager)
        data = {
            'brand': self.brand2.id,  # Trying to create for different brand
            'name': 'Cross Brand Category',
            'is_active': True
        }
        response = self.client.post('/api/categories/', data)
        
        # Should succeed but ignore the brand field and use manager's brand
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['brand'], self.brand1.id)  # Should be brand1, not brand2
    
    def test_orphan_brand_manager_cannot_create_category(self):
        """Test that brand manager without brand cannot create category."""
        self.client.force_authenticate(user=self.orphan_manager)
        data = {
            'name': 'Orphan Category',
            'is_active': True
        }
        response = self.client.post('/api/categories/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_admin_can_create_product_for_any_brand(self):
        """Test that admin can create product for any brand."""
        self.client.force_authenticate(user=self.admin_user)
        data = {
            'brand': self.brand2.id,
            'category': self.category2.id,
            'name': 'Admin Created Product',
            'sku': 'ADMIN-001',
            'price': 599.99,
            'is_active': True
        }
        response = self.client.post('/api/products/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['brand'], self.brand2.id)
    
    def test_brand_manager_creates_product_for_own_brand(self):
        """Test that brand manager automatically creates product for their brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        data = {
            'category': self.category1.id,
            'name': 'Brand Manager Product',
            'sku': 'BRAND-001',
            'price': 799.99,
            'is_active': True
        }
        response = self.client.post('/api/products/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['brand'], self.brand1.id)
    
    def test_brand_manager_cannot_create_product_for_other_brand(self):
        """Test that brand manager cannot specify other brand when creating product."""
        self.client.force_authenticate(user=self.brand1_manager)
        data = {
            'brand': self.brand2.id,  # Trying to create for different brand
            'name': 'Cross Brand Product',
            'sku': 'CROSS-001',
            'price': 699.99,
            'is_active': True
        }
        response = self.client.post('/api/products/', data)
        
        # Should succeed but ignore the brand field and use manager's brand
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['brand'], self.brand1.id)  # Should be brand1, not brand2
    
    def test_brand_manager_cannot_assign_category_from_other_brand(self):
        """Test that brand manager cannot assign category from other brand to product."""
        self.client.force_authenticate(user=self.brand1_manager)
        data = {
            'category': self.category2.id,  # Category from brand2
            'name': 'Invalid Category Product',
            'sku': 'INVALID-001',
            'price': 699.99,
            'is_active': True
        }
        response = self.client.post('/api/products/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)
    
    def test_orphan_brand_manager_cannot_create_product(self):
        """Test that brand manager without brand cannot create product."""
        self.client.force_authenticate(user=self.orphan_manager)
        data = {
            'name': 'Orphan Product',
            'sku': 'ORPHAN-001',
            'price': 499.99,
            'is_active': True
        }
        response = self.client.post('/api/products/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_unauthenticated_user_cannot_access_categories(self):
        """Test that unauthenticated users cannot access category endpoints."""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_unauthenticated_user_cannot_access_products(self):
        """Test that unauthenticated users cannot access product endpoints."""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_brand_manager_cannot_update_other_brand_category(self):
        """Test that brand manager cannot update category from another brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        data = {'name': 'Updated Category Name'}
        response = self.client.patch(f'/api/categories/{self.category2.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_brand_manager_cannot_update_other_brand_product(self):
        """Test that brand manager cannot update product from another brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        data = {'name': 'Updated Product Name'}
        response = self.client.patch(f'/api/products/{self.product2.id}/', data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_brand_manager_cannot_delete_other_brand_category(self):
        """Test that brand manager cannot delete category from another brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.delete(f'/api/categories/{self.category2.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_brand_manager_cannot_delete_other_brand_product(self):
        """Test that brand manager cannot delete product from another brand."""
        self.client.force_authenticate(user=self.brand1_manager)
        response = self.client.delete(f'/api/products/{self.product2.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)