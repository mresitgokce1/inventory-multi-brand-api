"""
Tests for filtering, search, and ordering functionality in catalog views.
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Brand, User
from catalog.models import Category, Product
from core.constants import ROLE_ADMIN, ROLE_BRAND_MANAGER


class TestCategoryFiltering(TestCase):
    """Test Category filtering, search, and ordering."""
    
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
        
        # Create categories
        self.category1 = Category.objects.create(
            brand=self.brand1,
            name="Electronics",
            is_active=True
        )
        
        self.category2 = Category.objects.create(
            brand=self.brand1,
            name="Gaming Equipment", 
            is_active=False
        )
        
        self.category3 = Category.objects.create(
            brand=self.brand2,
            name="Home Electronics",
            is_active=True
        )
        
        self.category4 = Category.objects.create(
            brand=self.brand2,
            name="Audio Equipment",
            is_active=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_category_filter_by_is_active(self):
        """Test filtering categories by is_active status."""
        response = self.client.get('/api/categories/?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        active_categories = [cat['id'] for cat in response.data['results']]
        self.assertIn(self.category1.id, active_categories)
        self.assertNotIn(self.category2.id, active_categories)
        self.assertIn(self.category3.id, active_categories)
        self.assertIn(self.category4.id, active_categories)
    
    def test_category_filter_by_name(self):
        """Test filtering categories by name (case-insensitive contains)."""
        response = self.client.get('/api/categories/?name=electronics')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category_ids = [cat['id'] for cat in response.data['results']]
        self.assertIn(self.category1.id, category_ids)
        self.assertIn(self.category3.id, category_ids)
        self.assertNotIn(self.category2.id, category_ids)
        self.assertNotIn(self.category4.id, category_ids)
    
    def test_category_search(self):
        """Test searching categories by name."""
        response = self.client.get('/api/categories/?search=gaming')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category_ids = [cat['id'] for cat in response.data['results']]
        self.assertIn(self.category2.id, category_ids)
        self.assertNotIn(self.category1.id, category_ids)
    
    def test_category_ordering_by_name(self):
        """Test ordering categories by name."""
        response = self.client.get('/api/categories/?ordering=name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category_names = [cat['name'] for cat in response.data['results']]
        self.assertEqual(category_names, sorted(category_names))
    
    def test_category_ordering_by_name_desc(self):
        """Test ordering categories by name descending."""
        response = self.client.get('/api/categories/?ordering=-name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category_names = [cat['name'] for cat in response.data['results']]
        self.assertEqual(category_names, sorted(category_names, reverse=True))
    
    def test_category_ordering_by_created_at(self):
        """Test ordering categories by creation date."""
        response = self.client.get('/api/categories/?ordering=created_at')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should be in creation order
        category_ids = [cat['id'] for cat in response.data['results']]
        expected_order = [self.category1.id, self.category2.id, 
                         self.category3.id, self.category4.id]
        self.assertEqual(category_ids, expected_order)
    
    def test_category_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client.get('/api/categories/?is_active=true&name=electronics&ordering=name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        category_ids = [cat['id'] for cat in response.data['results']]
        # Should include Electronics and Home Electronics, but not Gaming Equipment (inactive)
        self.assertIn(self.category1.id, category_ids)
        self.assertIn(self.category3.id, category_ids)
        self.assertNotIn(self.category2.id, category_ids)
        
        # Should be ordered by name
        category_names = [cat['name'] for cat in response.data['results']]
        self.assertEqual(category_names, sorted(category_names))


class TestProductFiltering(TestCase):
    """Test Product filtering, search, and ordering."""
    
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
        
        # Create categories
        self.category1 = Category.objects.create(brand=self.brand1, name="Laptops")
        self.category2 = Category.objects.create(brand=self.brand2, name="Tablets")
        
        # Create products with different attributes
        self.product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99,
            stock=10,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Business Laptop",
            sku="BUSINESS-001",
            price=899.99,
            stock=5,
            is_active=False
        )
        
        self.product3 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Pro Tablet",
            sku="TABLET-001",
            price=699.99,
            stock=15,
            is_active=True
        )
        
        self.product4 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Basic Tablet",
            sku="TABLET-002",
            price=299.99,
            stock=20,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_product_filter_by_category(self):
        """Test filtering products by category."""
        response = self.client.get(f'/api/products/?category={self.category1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.product1.id, product_ids)
        self.assertIn(self.product2.id, product_ids)
        self.assertNotIn(self.product3.id, product_ids)
        self.assertNotIn(self.product4.id, product_ids)
    
    def test_product_filter_by_is_active(self):
        """Test filtering products by is_active status."""
        response = self.client.get('/api/products/?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        active_products = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.product1.id, active_products)
        self.assertNotIn(self.product2.id, active_products)
        self.assertIn(self.product3.id, active_products)
        self.assertIn(self.product4.id, active_products)
    
    def test_product_filter_by_min_price(self):
        """Test filtering products by minimum price."""
        response = self.client.get('/api/products/?min_price=500')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.product1.id, product_ids)  # 1299.99
        self.assertIn(self.product2.id, product_ids)  # 899.99
        self.assertIn(self.product3.id, product_ids)  # 699.99
        self.assertNotIn(self.product4.id, product_ids)  # 299.99
    
    def test_product_filter_by_max_price(self):
        """Test filtering products by maximum price."""
        response = self.client.get('/api/products/?max_price=700')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertNotIn(self.product1.id, product_ids)  # 1299.99
        self.assertNotIn(self.product2.id, product_ids)  # 899.99
        self.assertIn(self.product3.id, product_ids)  # 699.99
        self.assertIn(self.product4.id, product_ids)  # 299.99
    
    def test_product_filter_by_price_range(self):
        """Test filtering products by price range."""
        response = self.client.get('/api/products/?min_price=300&max_price=900')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertNotIn(self.product1.id, product_ids)  # 1299.99
        self.assertIn(self.product2.id, product_ids)  # 899.99
        self.assertIn(self.product3.id, product_ids)  # 699.99
        self.assertNotIn(self.product4.id, product_ids)  # 299.99
    
    def test_product_filter_by_brand_admin_only(self):
        """Test filtering products by brand (admin only)."""
        response = self.client.get(f'/api/products/?brand={self.brand1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.product1.id, product_ids)
        self.assertIn(self.product2.id, product_ids)
        self.assertNotIn(self.product3.id, product_ids)
        self.assertNotIn(self.product4.id, product_ids)
    
    def test_product_search_by_name(self):
        """Test searching products by name."""
        response = self.client.get('/api/products/?search=laptop')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.product1.id, product_ids)
        self.assertIn(self.product2.id, product_ids)
        self.assertNotIn(self.product3.id, product_ids)
        self.assertNotIn(self.product4.id, product_ids)
    
    def test_product_search_by_sku(self):
        """Test searching products by SKU."""
        response = self.client.get('/api/products/?search=GAMING')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        self.assertIn(self.product1.id, product_ids)
        self.assertNotIn(self.product2.id, product_ids)
        self.assertNotIn(self.product3.id, product_ids)
        self.assertNotIn(self.product4.id, product_ids)
    
    def test_product_ordering_by_name(self):
        """Test ordering products by name."""
        response = self.client.get('/api/products/?ordering=name')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_names = [prod['name'] for prod in response.data['results']]
        self.assertEqual(product_names, sorted(product_names))
    
    def test_product_ordering_by_price(self):
        """Test ordering products by price."""
        response = self.client.get('/api/products/?ordering=price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prices = [float(prod['price']) for prod in response.data['results']]
        self.assertEqual(prices, sorted(prices))
    
    def test_product_ordering_by_price_desc(self):
        """Test ordering products by price descending."""
        response = self.client.get('/api/products/?ordering=-price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        prices = [float(prod['price']) for prod in response.data['results']]
        self.assertEqual(prices, sorted(prices, reverse=True))
    
    def test_product_ordering_by_stock(self):
        """Test ordering products by stock."""
        response = self.client.get('/api/products/?ordering=stock')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        stocks = [prod['stock'] for prod in response.data['results']]
        self.assertEqual(stocks, sorted(stocks))
    
    def test_product_ordering_by_created_at_default(self):
        """Test default ordering by created_at (newest first)."""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should be in reverse creation order (newest first)
        product_ids = [prod['id'] for prod in response.data['results']]
        expected_order = [self.product4.id, self.product3.id, 
                         self.product2.id, self.product1.id]
        self.assertEqual(product_ids, expected_order)
    
    def test_product_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client.get('/api/products/?is_active=true&min_price=600&search=tablet&ordering=price')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        # Should include Pro Tablet (699.99, active, contains "tablet")
        # Should not include Basic Tablet (299.99, below min_price)
        self.assertIn(self.product3.id, product_ids)
        self.assertNotIn(self.product4.id, product_ids)
        self.assertNotIn(self.product1.id, product_ids)
        self.assertNotIn(self.product2.id, product_ids)


class TestBrandManagerFiltering(TestCase):
    """Test that brand managers see appropriate filtered results."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create brands
        self.brand1 = Brand.objects.create(name="TechCorp", slug="techcorp")
        self.brand2 = Brand.objects.create(name="GadgetInc", slug="gadgetinc")
        
        # Create brand manager
        self.brand1_manager = User.objects.create_user(
            email="brand1@example.com",
            password="brand123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand1
        )
        
        # Create categories
        self.category1 = Category.objects.create(brand=self.brand1, name="Laptops")
        self.category2 = Category.objects.create(brand=self.brand2, name="Tablets")
        
        # Create products
        self.product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Pro Tablet",
            sku="TABLET-001",
            price=699.99,
            is_active=True
        )
        
        self.client.force_authenticate(user=self.brand1_manager)
    
    def test_brand_manager_filter_shows_only_own_brand(self):
        """Test that brand manager filters only apply to their own brand's data."""
        response = self.client.get('/api/products/?is_active=true')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        # Should only see own brand's products
        self.assertIn(self.product1.id, product_ids)
        self.assertNotIn(self.product2.id, product_ids)
    
    def test_brand_manager_cannot_filter_by_brand(self):
        """Test that brand filter doesn't apply for brand managers."""
        # Brand filter should be ignored for brand managers
        response = self.client.get(f'/api/products/?brand={self.brand2.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        product_ids = [prod['id'] for prod in response.data['results']]
        # Should still only see own brand's products, regardless of brand filter
        self.assertIn(self.product1.id, product_ids)
        self.assertNotIn(self.product2.id, product_ids)