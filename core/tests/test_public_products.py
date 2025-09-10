"""
Tests for public products endpoint.
"""
import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import Brand
from core.models import Category, Product


@pytest.mark.django_db
class TestPublicProducts:
    """
    Test public products endpoint functionality.
    """

    def setup_method(self):
        """Set up test data."""
        # Create brands
        self.brand1 = Brand.objects.create(name="Brand One", slug="brand-one")
        self.brand2 = Brand.objects.create(name="Brand Two", slug="brand-two")
        
        # Create categories
        self.category1 = Category.objects.create(
            brand=self.brand1,
            name="Electronics",
            slug="electronics"
        )
        
        self.category2 = Category.objects.create(
            brand=self.brand2,
            name="Clothing",
            slug="clothing"
        )
        
        # Create active products
        self.product1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Smartphone",
            sku="PHONE001",
            price=Decimal('599.99'),
            stock=10,
            is_active=True
        )
        
        self.product2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="T-Shirt",
            sku="SHIRT001",
            price=Decimal('29.99'),
            stock=25,
            is_active=True
        )
        
        # Create inactive product (should not appear in public endpoint)
        self.product3 = Product.objects.create(
            brand=self.brand1,
            name="Inactive Product",
            sku="INACTIVE001",
            price=Decimal('99.99'),
            stock=5,
            is_active=False
        )
        
        self.client = APIClient()
        # Note: No authentication - public endpoint

    def test_public_endpoint_allows_unauthenticated_access(self):
        """Test that public endpoint works without authentication."""
        response = self.client.get('/api/public/products/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data

    def test_public_endpoint_only_shows_active_products(self):
        """Test that only active products are shown in public endpoint."""
        response = self.client.get('/api/public/products/')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        
        # Should only show 2 active products
        assert len(results) == 2
        
        # Verify inactive product is not included
        product_ids = [p['id'] for p in results]
        assert self.product1.id in product_ids
        assert self.product2.id in product_ids
        assert self.product3.id not in product_ids

    def test_public_endpoint_limited_fields(self):
        """Test that public endpoint returns only intended fields."""
        response = self.client.get('/api/public/products/')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        
        if results:
            product = results[0]
            expected_fields = {'id', 'name', 'slug', 'price', 'image_small_url', 'brand', 'category'}
            actual_fields = set(product.keys())
            assert actual_fields == expected_fields
            
            # Check brand structure
            if product['brand']:
                brand_fields = set(product['brand'].keys())
                expected_brand_fields = {'id', 'name', 'slug'}
                assert brand_fields == expected_brand_fields
            
            # Check category structure
            if product['category']:
                category_fields = set(product['category'].keys())
                expected_category_fields = {'id', 'name', 'slug'}
                assert category_fields == expected_category_fields

    def test_filter_by_brand_slug(self):
        """Test filtering by brand slug."""
        response = self.client.get('/api/public/products/?brand=brand-one')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product1.id
        assert results[0]['brand']['slug'] == 'brand-one'

    def test_filter_by_category_id(self):
        """Test filtering by category ID."""
        response = self.client.get(f'/api/public/products/?category={self.category1.id}')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product1.id

    def test_filter_by_category_slug(self):
        """Test filtering by category slug."""
        response = self.client.get('/api/public/products/?category=clothing')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product2.id

    def test_filter_by_price_range(self):
        """Test filtering by price range."""
        # Test minimum price
        response = self.client.get('/api/public/products/?min_price=500')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product1.id
        
        # Test maximum price
        response = self.client.get('/api/public/products/?max_price=50')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product2.id

    def test_search_functionality(self):
        """Test search by name and SKU."""
        # Search by name
        response = self.client.get('/api/public/products/?search=smartphone')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product1.id
        
        # Search by SKU
        response = self.client.get('/api/public/products/?search=SHIRT001')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        assert len(results) == 1
        assert results[0]['id'] == self.product2.id

    def test_ordering_functionality(self):
        """Test ordering by different fields."""
        # Order by price ascending
        response = self.client.get('/api/public/products/?ordering=price')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        prices = [float(p['price']) for p in results]
        assert prices == sorted(prices)
        
        # Order by price descending
        response = self.client.get('/api/public/products/?ordering=-price')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        prices = [float(p['price']) for p in results]
        assert prices == sorted(prices, reverse=True)
        
        # Default ordering should be by created_at descending
        response = self.client.get('/api/public/products/')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        # Since product2 was created after product1, it should come first
        assert results[0]['id'] == self.product2.id
        assert results[1]['id'] == self.product1.id

    def test_invalid_ordering_uses_default(self):
        """Test that invalid ordering parameter uses default ordering."""
        response = self.client.get('/api/public/products/?ordering=invalid_field')
        
        assert response.status_code == status.HTTP_200_OK
        results = response.data['results']
        # Should fall back to default ordering (-created_at)
        assert len(results) == 2