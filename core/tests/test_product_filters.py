"""
Tests for product filtering functionality.
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from accounts.models import Brand
from core.constants import ROLE_ADMIN, ROLE_BRAND_MANAGER
from core.models import Category, Product

User = get_user_model()


@pytest.mark.django_db
class TestProductFilters:
    """
    Test product filtering, search, and ordering functionality.
    """

    def setup_method(self):
        """Set up test data."""
        # Create brand
        self.brand = Brand.objects.create(name="Test Brand")
        
        # Create admin user
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="testpass123",
            role=ROLE_ADMIN
        )
        
        # Create category
        self.category = Category.objects.create(
            brand=self.brand,
            name="Electronics"
        )
        
        # Create products with different attributes
        self.product1 = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name="Laptop Computer",
            sku="LAPTOP001",
            price=Decimal('1200.00'),
            stock=5,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            brand=self.brand,
            category=self.category,
            name="Wireless Mouse",
            sku="MOUSE001", 
            price=Decimal('25.50'),
            stock=15,
            is_active=True
        )
        
        self.product3 = Product.objects.create(
            brand=self.brand,
            name="Keyboard USB",
            sku="KEYB001",
            price=Decimal('65.00'),
            stock=0,
            is_active=False
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_filter_by_category(self):
        """Test filtering products by category."""
        response = self.client.get(f'/api/products/?category={self.category.id}')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 2  # Only products with category
        
        product_ids = [p['id'] for p in results]
        assert self.product1.id in product_ids
        assert self.product2.id in product_ids
        assert self.product3.id not in product_ids

    def test_filter_by_active_status(self):
        """Test filtering products by active status."""
        # Test active products
        response = self.client.get('/api/products/?is_active=true')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 2
        
        # Test inactive products
        response = self.client.get('/api/products/?is_active=false')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product3.id

    def test_filter_by_price_range(self):
        """Test filtering products by price range."""
        # Test minimum price
        response = self.client.get('/api/products/?min_price=100')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product1.id
        
        # Test maximum price
        response = self.client.get('/api/products/?max_price=50')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product2.id
        
        # Test price range
        response = self.client.get('/api/products/?min_price=20&max_price=100')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 2
        product_ids = [p['id'] for p in results]
        assert self.product2.id in product_ids
        assert self.product3.id in product_ids

    def test_search_by_name_and_sku(self):
        """Test searching products by name and SKU."""
        # Search by name
        response = self.client.get('/api/products/?search=laptop')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product1.id
        
        # Search by SKU
        response = self.client.get('/api/products/?search=MOUSE001')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product2.id
        
        # Search partial match
        response = self.client.get('/api/products/?search=mouse')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product2.id

    def test_ordering_by_price(self):
        """Test ordering products by price."""
        # Order by price ascending
        response = self.client.get('/api/products/?ordering=price')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        prices = [float(p['price']) for p in results]
        assert prices == sorted(prices)
        
        # Order by price descending
        response = self.client.get('/api/products/?ordering=-price')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        prices = [float(p['price']) for p in results]
        assert prices == sorted(prices, reverse=True)

    def test_combined_filters(self):
        """Test combining multiple filters."""
        response = self.client.get(
            f'/api/products/?category={self.category.id}&is_active=true&min_price=20&max_price=100'
        )
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product2.id