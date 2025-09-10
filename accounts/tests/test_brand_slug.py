import pytest
from accounts.models import Brand


@pytest.mark.django_db
class TestBrandSlugGeneration:
    """Test Brand slug auto-generation functionality."""

    def test_slug_auto_generation(self):
        """Test that slug is auto-generated from name."""
        brand = Brand.objects.create(name="Test Brand Company")
        
        assert brand.slug == "test-brand-company"
        assert brand.name == "Test Brand Company"

    def test_slug_manual_override(self):
        """Test that manually provided slug is preserved."""
        brand = Brand.objects.create(
            name="Test Brand Company",
            slug="custom-slug"
        )
        
        assert brand.slug == "custom-slug"
        assert brand.name == "Test Brand Company"

    def test_slug_unique_constraint(self):
        """Test that slug must be unique."""
        Brand.objects.create(name="Brand One")
        
        # Create another brand that would generate the same slug
        with pytest.raises(Exception):  # IntegrityError
            Brand.objects.create(name="Brand One")

    def test_slug_with_special_characters(self):
        """Test slug generation with special characters."""
        brand = Brand.objects.create(name="Brand & Company Ltd.")
        
        assert brand.slug == "brand-company-ltd"

    def test_slug_with_unicode_characters(self):
        """Test slug generation with unicode characters."""
        brand = Brand.objects.create(name="Café Müller")
        
        assert brand.slug == "cafe-muller"

    def test_brand_str_representation(self):
        """Test Brand string representation."""
        brand = Brand.objects.create(name="Test Brand")
        
        assert str(brand) == "Test Brand"

    def test_brand_ordering(self):
        """Test Brand model ordering by name."""
        Brand.objects.create(name="Z Brand")
        Brand.objects.create(name="A Brand")
        Brand.objects.create(name="M Brand")
        
        brands = list(Brand.objects.all())
        brand_names = [brand.name for brand in brands]
        
        assert brand_names == ["A Brand", "M Brand", "Z Brand"]