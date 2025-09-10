from django.db import models
from django.core.exceptions import ValidationError
from slugify import slugify
from accounts.models import Brand


class Category(models.Model):
    """
    Category model with brand-scoped uniqueness.
    """
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['brand', 'name'],
                name='unique_category_brand_name'
            ),
            models.UniqueConstraint(
                fields=['brand', 'slug'],
                name='unique_category_brand_slug'
            )
        ]
        ordering = ['brand', 'name']

    def __str__(self):
        return f"{self.brand.name} - {self.name}"

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided, with collision handling.
        """
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 2
            
            # Check for slug collisions within the same brand
            while Category.objects.filter(brand=self.brand, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Product model with brand-scoped uniqueness.
    """
    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    sku = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    image_small = models.ImageField(upload_to='products/small/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['brand', 'sku'],
                name='unique_product_brand_sku'
            ),
            models.UniqueConstraint(
                fields=['brand', 'slug'],
                name='unique_product_brand_slug'
            )
        ]
        ordering = ['brand', 'name']

    def __str__(self):
        return f"{self.brand.name} - {self.name}"

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided, with collision handling.
        """
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 2
            
            # Check for slug collisions within the same brand
            while Product.objects.filter(brand=self.brand, slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
