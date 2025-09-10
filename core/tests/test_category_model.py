"""
Tests for Category model functionality.
"""
import pytest
from django.db.utils import IntegrityError
from accounts.models import Brand
from core.models import Category


@pytest.mark.django_db
class TestCategoryModel:
    """
    Test Category model functionality.
    """

    def test_category_creation(self):
        """Test basic category creation."""
        brand = Brand.objects.create(name="Test Brand")
        category = Category.objects.create(
            brand=brand,
            name="Test Category"
        )
        
        assert category.id is not None
        assert category.name == "Test Category"
        assert category.brand == brand
        assert category.is_active is True
        assert category.slug == "test-category"  # Auto-generated

    def test_category_slug_auto_generation(self):
        """Test automatic slug generation from name."""
        brand = Brand.objects.create(name="Test Brand")
        category = Category.objects.create(
            brand=brand,
            name="My Special Category!"
        )
        
        assert category.slug == "my-special-category"

    def test_category_slug_manual_override(self):
        """Test manual slug override."""
        brand = Brand.objects.create(name="Test Brand")
        category = Category.objects.create(
            brand=brand,
            name="Test Category",
            slug="custom-slug"
        )
        
        assert category.slug == "custom-slug"

    def test_category_unique_name_per_brand(self):
        """Test that category names must be unique per brand."""
        brand1 = Brand.objects.create(name="Brand 1")
        brand2 = Brand.objects.create(name="Brand 2")
        
        # Same name in different brands should work
        Category.objects.create(brand=brand1, name="Electronics")
        Category.objects.create(brand=brand2, name="Electronics")
        
        # Same name in same brand should fail
        with pytest.raises(IntegrityError):
            Category.objects.create(brand=brand1, name="Electronics")

    def test_category_unique_slug_per_brand(self):
        """Test that category slugs must be unique per brand."""
        brand1 = Brand.objects.create(name="Brand 1")
        brand2 = Brand.objects.create(name="Brand 2")
        
        # Same slug in different brands should work
        Category.objects.create(brand=brand1, name="Electronics", slug="electronics")
        Category.objects.create(brand=brand2, name="Electronics", slug="electronics")
        
        # Same slug in same brand should fail
        with pytest.raises(IntegrityError):
            Category.objects.create(brand=brand1, name="Electronic Devices", slug="electronics")

    def test_category_str_representation(self):
        """Test string representation of category."""
        brand = Brand.objects.create(name="Test Brand")
        category = Category.objects.create(
            brand=brand,
            name="Test Category"
        )
        
        expected = "Test Brand - Test Category"
        assert str(category) == expected

    def test_category_ordering(self):
        """Test that categories are ordered by name."""
        brand = Brand.objects.create(name="Test Brand")
        
        category_b = Category.objects.create(brand=brand, name="B Category")
        category_a = Category.objects.create(brand=brand, name="A Category")
        category_c = Category.objects.create(brand=brand, name="C Category")
        
        categories = list(Category.objects.all())
        assert categories == [category_a, category_b, category_c]