"""
Tests for catalog models: constraints, slug generation, and collision handling.
"""
import pytest
from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from accounts.models import Brand
from catalog.models import Category, Product


class TestCategoryModel(TestCase):
    """Test Category model constraints and behavior."""
    
    def setUp(self):
        """Set up test data."""
        self.brand1 = Brand.objects.create(name="TechCorp", slug="techcorp")
        self.brand2 = Brand.objects.create(name="GadgetInc", slug="gadgetinc")
    
    def test_category_brand_name_unique_constraint(self):
        """Test that category name must be unique within a brand."""
        # Create category
        Category.objects.create(brand=self.brand1, name="Electronics")
        
        # Try to create duplicate in same brand - should fail
        with self.assertRaises(IntegrityError):
            Category.objects.create(brand=self.brand1, name="Electronics")
    
    def test_category_name_unique_across_brands(self):
        """Test that category name can be duplicated across different brands."""
        # Create category in brand1
        cat1 = Category.objects.create(brand=self.brand1, name="Electronics")
        
        # Create same name in brand2 - should succeed
        cat2 = Category.objects.create(brand=self.brand2, name="Electronics")
        
        self.assertEqual(cat1.name, cat2.name)
        self.assertNotEqual(cat1.brand, cat2.brand)
    
    def test_category_brand_slug_unique_constraint(self):
        """Test that category slug must be unique within a brand."""
        # Create category
        Category.objects.create(brand=self.brand1, name="Electronics", slug="electronics")
        
        # Try to create duplicate slug in same brand - should fail
        with self.assertRaises(IntegrityError):
            Category.objects.create(brand=self.brand1, name="Electronic Items", slug="electronics")
    
    def test_category_slug_unique_across_brands(self):
        """Test that category slug can be duplicated across different brands."""
        # Create category in brand1
        cat1 = Category.objects.create(brand=self.brand1, name="Electronics", slug="electronics")
        
        # Create same slug in brand2 - should succeed
        cat2 = Category.objects.create(brand=self.brand2, name="Electronic Gadgets", slug="electronics")
        
        self.assertEqual(cat1.slug, cat2.slug)
        self.assertNotEqual(cat1.brand, cat2.brand)
    
    def test_category_slug_auto_generation(self):
        """Test automatic slug generation from name."""
        category = Category.objects.create(brand=self.brand1, name="Gaming Laptops")
        self.assertEqual(category.slug, "gaming-laptops")
    
    def test_category_slug_collision_handling(self):
        """Test slug collision handling with auto-increment."""
        # Create first category
        cat1 = Category.objects.create(brand=self.brand1, name="Gaming")
        self.assertEqual(cat1.slug, "gaming")
        
        # Create second category that would generate the same slug
        # The name is different but would slugify to "gaming" 
        cat2 = Category.objects.create(brand=self.brand1, name="Gaming!")  # Special chars get stripped
        self.assertEqual(cat2.slug, "gaming-2")
        
        # Create third category that would generate the same base slug
        cat3 = Category.objects.create(brand=self.brand1, name="Gaming?")  # Another that slugifies to "gaming"
        self.assertEqual(cat3.slug, "gaming-3")
    
    def test_category_slug_collision_across_brands(self):
        """Test that slug collision handling is per-brand."""
        # Create category in brand1
        cat1 = Category.objects.create(brand=self.brand1, name="Gaming")
        self.assertEqual(cat1.slug, "gaming")
        
        # Create same base name in brand2 - should not collide
        cat2 = Category.objects.create(brand=self.brand2, name="Gaming")
        self.assertEqual(cat2.slug, "gaming")  # No collision across brands
    
    def test_category_manual_slug_override(self):
        """Test manual slug override works."""
        category = Category.objects.create(
            brand=self.brand1, 
            name="Gaming Laptops", 
            slug="custom-gaming-slug"
        )
        self.assertEqual(category.slug, "custom-gaming-slug")
    
    def test_category_str_representation(self):
        """Test category string representation."""
        category = Category.objects.create(brand=self.brand1, name="Electronics")
        expected = f"{self.brand1.name} - Electronics"
        self.assertEqual(str(category), expected)


class TestProductModel(TestCase):
    """Test Product model constraints and behavior."""
    
    def setUp(self):
        """Set up test data."""
        self.brand1 = Brand.objects.create(name="TechCorp", slug="techcorp")
        self.brand2 = Brand.objects.create(name="GadgetInc", slug="gadgetinc")
        self.category1 = Category.objects.create(brand=self.brand1, name="Laptops")
        self.category2 = Category.objects.create(brand=self.brand2, name="Laptops")
    
    def test_product_brand_sku_unique_constraint(self):
        """Test that product SKU must be unique within a brand."""
        # Create product
        Product.objects.create(
            brand=self.brand1, 
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99
        )
        
        # Try to create duplicate SKU in same brand - should fail
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                brand=self.brand1,
                category=self.category1,
                name="Different Laptop",
                sku="GAMING-001",
                price=999.99
            )
    
    def test_product_sku_unique_across_brands(self):
        """Test that product SKU can be duplicated across different brands."""
        # Create product in brand1
        prod1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99
        )
        
        # Create same SKU in brand2 - should succeed
        prod2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Different Gaming Laptop",
            sku="GAMING-001",
            price=1499.99
        )
        
        self.assertEqual(prod1.sku, prod2.sku)
        self.assertNotEqual(prod1.brand, prod2.brand)
    
    def test_product_brand_slug_unique_constraint(self):
        """Test that product slug must be unique within a brand."""
        # Create product
        Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            slug="gaming-laptop",
            price=1299.99
        )
        
        # Try to create duplicate slug in same brand - should fail
        with self.assertRaises(IntegrityError):
            Product.objects.create(
                brand=self.brand1,
                category=self.category1,
                name="Different Gaming Laptop",
                sku="GAMING-002",
                slug="gaming-laptop",
                price=999.99
            )
    
    def test_product_slug_unique_across_brands(self):
        """Test that product slug can be duplicated across different brands."""
        # Create product in brand1
        prod1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            slug="gaming-laptop",
            price=1299.99
        )
        
        # Create same slug in brand2 - should succeed
        prod2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Gaming Laptop Model X",
            sku="GAMING-001",
            slug="gaming-laptop",
            price=1499.99
        )
        
        self.assertEqual(prod1.slug, prod2.slug)
        self.assertNotEqual(prod1.brand, prod2.brand)
    
    def test_product_slug_auto_generation(self):
        """Test automatic slug generation from name."""
        product = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="High-End Gaming Laptop",
            sku="GAMING-001",
            price=1299.99
        )
        self.assertEqual(product.slug, "high-end-gaming-laptop")
    
    def test_product_slug_collision_handling(self):
        """Test slug collision handling with auto-increment."""
        # Create first product
        prod1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99
        )
        self.assertEqual(prod1.slug, "gaming-laptop")
        
        # Create second product that would generate the same slug
        prod2 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop!",  # Would slugify to "gaming-laptop"
            sku="GAMING-002",
            price=1599.99
        )
        self.assertEqual(prod2.slug, "gaming-laptop-2")
        
        # Create third product that would generate the same base slug
        prod3 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop?",  # Would also slugify to "gaming-laptop"
            sku="GAMING-003",
            price=1899.99
        )
        self.assertEqual(prod3.slug, "gaming-laptop-3")
    
    def test_product_slug_collision_across_brands(self):
        """Test that slug collision handling is per-brand."""
        # Create product in brand1
        prod1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99
        )
        self.assertEqual(prod1.slug, "gaming-laptop")
        
        # Create same base name in brand2 - should not collide
        prod2 = Product.objects.create(
            brand=self.brand2,
            category=self.category2,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1399.99
        )
        self.assertEqual(prod2.slug, "gaming-laptop")  # No collision across brands
    
    def test_product_manual_slug_override(self):
        """Test manual slug override works."""
        product = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            slug="custom-gaming-slug",
            price=1299.99
        )
        self.assertEqual(product.slug, "custom-gaming-slug")
    
    def test_product_str_representation(self):
        """Test product string representation."""
        product = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Gaming Laptop",
            sku="GAMING-001",
            price=1299.99
        )
        expected = f"{self.brand1.name} - Gaming Laptop"
        self.assertEqual(str(product), expected)
    
    def test_product_ordering(self):
        """Test product default ordering."""
        # Create products in different order
        prod2 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="Z Laptop",
            sku="Z-001",
            price=999.99
        )
        prod1 = Product.objects.create(
            brand=self.brand1,
            category=self.category1,
            name="A Laptop",
            sku="A-001",
            price=899.99
        )
        
        # Check default ordering (by brand, then name)
        products = list(Product.objects.all())
        self.assertEqual(products[0], prod1)  # A Laptop comes first
        self.assertEqual(products[1], prod2)  # Z Laptop comes second