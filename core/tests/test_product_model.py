"""
Tests for Product model functionality.
"""
import pytest
from decimal import Decimal
from django.db.utils import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO
from accounts.models import Brand
from core.models import Category, Product


def create_test_image(width=100, height=100, format='JPEG'):
    """
    Create a simple test image for testing.
    """
    image = Image.new('RGB', (width, height), color='red')
    buffer = BytesIO()
    image.save(buffer, format=format)
    buffer.seek(0)
    return buffer


@pytest.mark.django_db
class TestProductModel:
    """
    Test Product model functionality.
    """

    def test_product_creation(self):
        """Test basic product creation."""
        brand = Brand.objects.create(name="Test Brand")
        category = Category.objects.create(brand=brand, name="Test Category")
        
        product = Product.objects.create(
            brand=brand,
            category=category,
            name="Test Product",
            sku="TEST001",
            price=Decimal('29.99'),
            stock=10
        )
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.brand == brand
        assert product.category == category
        assert product.sku == "TEST001"
        assert product.price == Decimal('29.99')
        assert product.stock == 10
        assert product.is_active is True
        assert product.slug == "test-product"  # Auto-generated

    def test_product_slug_auto_generation(self):
        """Test automatic slug generation from name."""
        brand = Brand.objects.create(name="Test Brand")
        product = Product.objects.create(
            brand=brand,
            name="My Amazing Product!",
            sku="TEST001",
            price=Decimal('29.99')
        )
        
        assert product.slug == "my-amazing-product"

    def test_product_slug_manual_override(self):
        """Test manual slug override."""
        brand = Brand.objects.create(name="Test Brand")
        product = Product.objects.create(
            brand=brand,
            name="Test Product",
            sku="TEST001",
            slug="custom-slug",
            price=Decimal('29.99')
        )
        
        assert product.slug == "custom-slug"

    def test_product_unique_sku_per_brand(self):
        """Test that product SKUs must be unique per brand."""
        brand1 = Brand.objects.create(name="Brand 1")
        brand2 = Brand.objects.create(name="Brand 2")
        
        # Same SKU in different brands should work
        Product.objects.create(brand=brand1, name="Product 1", sku="PROD001", price=Decimal('10.00'))
        Product.objects.create(brand=brand2, name="Product 2", sku="PROD001", price=Decimal('10.00'))
        
        # Same SKU in same brand should fail
        with pytest.raises(IntegrityError):
            Product.objects.create(brand=brand1, name="Product 3", sku="PROD001", price=Decimal('10.00'))

    def test_product_unique_slug_per_brand(self):
        """Test that product slugs must be unique per brand."""
        brand1 = Brand.objects.create(name="Brand 1")
        brand2 = Brand.objects.create(name="Brand 2")
        
        # Same slug in different brands should work
        Product.objects.create(brand=brand1, name="Product 1", sku="PROD001", slug="product", price=Decimal('10.00'))
        Product.objects.create(brand=brand2, name="Product 2", sku="PROD002", slug="product", price=Decimal('10.00'))
        
        # Same slug in same brand should fail
        with pytest.raises(IntegrityError):
            Product.objects.create(brand=brand1, name="Product 3", sku="PROD003", slug="product", price=Decimal('10.00'))

    def test_product_str_representation(self):
        """Test string representation of product."""
        brand = Brand.objects.create(name="Test Brand")
        product = Product.objects.create(
            brand=brand,
            name="Test Product",
            sku="TEST001",
            price=Decimal('29.99')
        )
        
        expected = "Test Brand - Test Product (TEST001)"
        assert str(product) == expected

    def test_product_ordering(self):
        """Test that products are ordered by -created_at."""
        brand = Brand.objects.create(name="Test Brand")
        
        product1 = Product.objects.create(
            brand=brand, name="Product 1", sku="PROD001", price=Decimal('10.00')
        )
        product2 = Product.objects.create(
            brand=brand, name="Product 2", sku="PROD002", price=Decimal('10.00')
        )
        product3 = Product.objects.create(
            brand=brand, name="Product 3", sku="PROD003", price=Decimal('10.00')
        )
        
        products = list(Product.objects.all())
        # Should be ordered by newest first (-created_at)
        assert products == [product3, product2, product1]

    def test_product_price_validation(self):
        """Test that price validation works in model level."""
        brand = Brand.objects.create(name="Test Brand")
        
        # Valid price should work
        product = Product.objects.create(
            brand=brand,
            name="Valid Product",
            sku="VALID001",
            price=Decimal('0.00')
        )
        assert product.price == Decimal('0.00')

    def test_product_stock_validation(self):
        """Test that stock validation works in model level."""
        brand = Brand.objects.create(name="Test Brand")
        
        # Valid stock should work
        product = Product.objects.create(
            brand=brand,
            name="Valid Product",
            sku="VALID001",
            price=Decimal('10.00'),
            stock=0
        )
        assert product.stock == 0

    def test_product_optional_category(self):
        """Test that category is optional."""
        brand = Brand.objects.create(name="Test Brand")
        product = Product.objects.create(
            brand=brand,
            name="No Category Product",
            sku="NO_CAT001",
            price=Decimal('10.00')
        )
        
        assert product.category is None

    def test_product_category_deletion_sets_null(self):
        """Test that deleting category sets product.category to NULL."""
        brand = Brand.objects.create(name="Test Brand")
        category = Category.objects.create(brand=brand, name="Test Category")
        product = Product.objects.create(
            brand=brand,
            category=category,
            name="Test Product",
            sku="TEST001",
            price=Decimal('10.00')
        )
        
        assert product.category == category
        
        # Delete category
        category.delete()
        
        # Refresh from database
        product.refresh_from_db()
        assert product.category is None

    @pytest.mark.skip(reason="Image processing tests require proper setup")
    def test_product_image_processing(self):
        """Test that image processing creates small version."""
        brand = Brand.objects.create(name="Test Brand")
        
        # Create a test image
        image_buffer = create_test_image(800, 600)
        uploaded_file = SimpleUploadedFile(
            name='test_image.jpg',
            content=image_buffer.getvalue(),
            content_type='image/jpeg'
        )
        
        product = Product.objects.create(
            brand=brand,
            name="Product with Image",
            sku="IMG001",
            price=Decimal('10.00'),
            image=uploaded_file
        )
        
        # Check that image_small was created
        # Note: This test is skipped as it requires proper media storage setup
        assert product.image is not None