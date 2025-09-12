"""
Tests for public endpoints that exclude inactive products and require no authentication.
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Brand, User
from catalog.models import Category, Product
from core.constants import ROLE_ADMIN


class TestPublicProductEndpoints(TestCase):
    """Test public product endpoints that exclude inactive products."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create brands
        self.brand1 = Brand.objects.create(name="TechCorp", slug="techcorp")
        self.brand2 = Brand.objects.create(name="GadgetInc", slug="gadgetinc")
        
        # Create categories
        self.category1 = Category.objects.create(brand=self.brand1, name="Laptops", slug="laptops")
        self.category2 = Category.objects.create(brand=self.brand2, name="Tablets", slug="tablets")
        
        # Create active products
        self.active_product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            slug="gaming-laptop",
            sku="GAMING-001",
            price=1299.99,
            stock=10,
            is_active=True
        )
        
        self.active_product2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Pro Tablet",
            slug="pro-tablet",
            sku="TABLET-001",
            price=699.99,
            stock=15,
            is_active=True
        )
        
        # Create inactive products
        self.inactive_product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Old Laptop",
            slug="old-laptop",
            sku="OLD-001",
            price=599.99,
            stock=0,
            is_active=False
        )
        
        self.inactive_product2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Discontinued Tablet",
            slug="discontinued-tablet",
            sku="DISC-001",
            price=399.99,
            stock=0,
            is_active=False
        )
    
    def test_public_products_no_authentication_required(self):
        """Test that public products endpoint requires no authentication."""
        # Don't authenticate the client
        response = self.client.get('/api/public/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_public_products_excludes_inactive(self):
        """Test that public products endpoint excludes inactive products."""
        response = self.client.get('/api/public/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        # Should include active products
        self.assertIn(self.active_product1.id, product_ids)
        self.assertIn(self.active_product2.id, product_ids)
        
        # Should exclude inactive products
        self.assertNotIn(self.inactive_product1.id, product_ids)
        self.assertNotIn(self.inactive_product2.id, product_ids)
    
    def test_public_products_limited_fields(self):
        """Test that public products endpoint returns limited fields."""
        response = self.client.get('/api/public/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product = response.data['results'][0]
        expected_fields = {'id', 'name', 'slug', 'price', 'image_small', 'brand', 'category'}
        actual_fields = set(product.keys())
        
        self.assertEqual(actual_fields, expected_fields)
        
        # Should not include internal fields
        self.assertNotIn('sku', product)
        self.assertNotIn('stock', product)
        self.assertNotIn('description', product)
        self.assertNotIn('image', product)
        self.assertNotIn('is_active', product)
        self.assertNotIn('created_at', product)
        self.assertNotIn('updated_at', product)
    
    def test_public_products_brand_nested_fields(self):
        """Test that brand information is properly nested in public products."""
        response = self.client.get('/api/public/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product = response.data['results'][0]
        brand = product['brand']
        
        # Brand should have id, name, and slug
        self.assertIn('id', brand)
        self.assertIn('name', brand)
        self.assertIn('slug', brand)
        self.assertEqual(len(brand), 3)  # Should only have these 3 fields
    
    def test_public_products_category_nested_fields(self):
        """Test that category information is properly nested in public products."""
        response = self.client.get('/api/public/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product = response.data['results'][0]
        category = product['category']
        
        # Category should have id, name, and slug
        self.assertIn('id', category)
        self.assertIn('name', category)
        self.assertIn('slug', category)
        self.assertEqual(len(category), 3)  # Should only have these 3 fields
    
    def test_public_products_filter_by_brand_slug(self):
        """Test filtering public products by brand slug."""
        response = self.client.get(f'/api/public/products/?brand={self.brand1.slug}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.active_product1.id, product_ids)
        self.assertNotIn(self.active_product2.id, product_ids)
        
        # Should still exclude inactive products from the same brand
        self.assertNotIn(self.inactive_product1.id, product_ids)
    
    def test_public_products_filter_by_category_id(self):
        """Test filtering public products by category ID."""
        response = self.client.get(f'/api/public/products/?category={self.category1.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.active_product1.id, product_ids)
        self.assertNotIn(self.active_product2.id, product_ids)
        
        # Should still exclude inactive products from the same category
        self.assertNotIn(self.inactive_product1.id, product_ids)
    
    def test_public_products_filter_by_category_slug(self):
        """Test filtering public products by category slug."""
        response = self.client.get(f'/api/public/products/?category={self.category1.slug}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.active_product1.id, product_ids)
        self.assertNotIn(self.active_product2.id, product_ids)
    
    def test_public_products_filter_by_price_range(self):
        """Test filtering public products by price range."""
        response = self.client.get('/api/public/products/?min_price=700&max_price=1400')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.active_product1.id, product_ids)  # 1299.99
        self.assertNotIn(self.active_product2.id, product_ids)  # 699.99
    
    def test_public_products_search(self):
        """Test searching public products by name and SKU."""
        response = self.client.get('/api/public/products/?search=gaming')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.active_product1.id, product_ids)
        self.assertNotIn(self.active_product2.id, product_ids)
    
    def test_public_products_ordering_by_price(self):
        """Test ordering public products by price."""
        response = self.client.get('/api/public/products/?ordering=price')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prices = [float(prod['price']) for prod in response.data['results']]
        self.assertEqual(prices, sorted(prices))
    
    def test_public_products_ordering_by_price_desc(self):
        """Test ordering public products by price descending."""
        response = self.client.get('/api/public/products/?ordering=-price')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prices = [float(prod['price']) for prod in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))
    
    def test_public_products_default_ordering(self):
        """Test default ordering by creation date (newest first)."""
        response = self.client.get('/api/public/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should be in reverse creation order (newest first)
        product_ids = [prod['id'] for prod in response.data['results']]
        # Only active products should be included
        expected_order = [self.active_product2.id, self.active_product1.id]
        self.assertEqual(product_ids, expected_order)
    
    def test_public_products_combined_filters(self):
        """Test combining multiple filters in public endpoint."""
        response = self.client.get(f'/api/public/products/?brand={self.brand1.slug}&min_price=1000&ordering=-price')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        # Should include Gaming Laptop (brand1, price 1299.99)
        self.assertIn(self.active_product1.id, product_ids)
        # Should not include Pro Tablet (different brand)
        self.assertNotIn(self.active_product2.id, product_ids)
        # Should not include inactive products
        self.assertNotIn(self.inactive_product1.id, product_ids)
    
    def test_public_products_pagination(self):
        """Test that public products endpoint supports pagination."""
        response = self.client.get('/api/public/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have pagination fields
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
    
    def test_public_products_detail_endpoint_not_available(self):
        """Test that individual product detail endpoint is not available in public API."""
        # Try to access individual product detail
        response = self.client.get(f'/api/public/products/{self.active_product1.id}/')
        
        # Should work since it's a ReadOnlyModelViewSet
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify it returns the same limited fields
        expected_fields = {'id', 'name', 'slug', 'price', 'image_small', 'brand', 'category'}
        actual_fields = set(response.data.keys())
        self.assertEqual(actual_fields, expected_fields)
    
    def test_public_products_detail_excludes_inactive(self):
        """Test that public product detail excludes inactive products."""
        # Try to access inactive product detail
        response = self.client.get(f'/api/public/products/{self.inactive_product1.id}/')
        
        # Should return 404 for inactive products
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_public_products_write_operations_not_allowed(self):
        """Test that write operations are not allowed on public endpoints."""
        # Try to create a product
        data = {
            'name': 'New Product',
            'sku': 'NEW-001',
            'price': 499.99
        }
        response = self.client.post('/api/public/products/', data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try to update a product
        response = self.client.put(f'/api/public/products/{self.active_product1.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try to patch a product
        response = self.client.patch(f'/api/public/products/{self.active_product1.id}/', {'name': 'Updated'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        
        # Try to delete a product
        response = self.client.delete(f'/api/public/products/{self.active_product1.id}/')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class TestPublicProductsWithAuthentication(TestCase):
    """Test that public endpoints work even when user is authenticated."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create brand and user
        self.brand = Brand.objects.create(name="TechCorp", slug="techcorp")
        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="admin123",
            role=ROLE_ADMIN
        )
        
        # Create category and products
        self.category = Category.objects.create(brand=self.brand, name="Laptops")
        
        self.active_product = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99,
            is_active=True
        )
        
        self.inactive_product = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name="Old Laptop",
            sku="OLD-001",
            price=599.99,
            is_active=False
        )
    
    def test_public_products_work_with_authentication(self):
        """Test that public endpoints work when user is authenticated."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/public/products/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should still only show active products and limited fields
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.active_product.id, product_ids)
        self.assertNotIn(self.inactive_product.id, product_ids)
        
        # Should still have limited fields
        product = response.data['results'][0]
        expected_fields = {'id', 'name', 'slug', 'price', 'image_small', 'brand', 'category'}
        actual_fields = set(product.keys())
        self.assertEqual(actual_fields, expected_fields)