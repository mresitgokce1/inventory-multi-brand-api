from django.db import models
from django.core.validators import MinValueValidator
from slugify import slugify
from accounts.models import Brand
from .images import process_product_image
import logging

logger = logging.getLogger(__name__)


class Category(models.Model):
    """
    Category model for organizing products within brands.
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
        verbose_name_plural = 'Categories'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['brand', 'name'],
                name='uniq_category_brand_name'
            ),
            models.UniqueConstraint(
                fields=['brand', 'slug'],
                name='uniq_category_brand_slug'
            ),
        ]

    def __str__(self):
        return f"{self.brand.name} - {self.name}"

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """
    Product model for inventory items within brands.
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
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    is_active = models.BooleanField(default=True)
    image = models.ImageField(
        upload_to='products/original/',
        blank=True,
        null=True
    )
    image_small = models.ImageField(
        upload_to='products/small/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['brand', 'sku'],
                name='uniq_product_brand_sku'
            ),
            models.UniqueConstraint(
                fields=['brand', 'slug'],
                name='uniq_product_brand_slug'
            ),
        ]

    def __str__(self):
        return f"{self.brand.name} - {self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name and process images if provided.
        """
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.name)

        # Check if this is an update with a new image
        process_image = False
        if self.pk:
            try:
                old_product = Product.objects.get(pk=self.pk)
                if self.image and self.image != old_product.image:
                    process_image = True
            except Product.DoesNotExist:
                pass
        elif self.image:
            # New product with image
            process_image = True

        super().save(*args, **kwargs)

        # Process image after saving to have the slug available
        if process_image and self.image:
            try:
                processed_original, small_image = process_product_image(
                    self.image.file, self.slug
                )
                
                if processed_original:
                    # Update the original image with processed version
                    self.image.save(
                        processed_original.name,
                        processed_original,
                        save=False
                    )
                
                if small_image:
                    # Save the small image
                    self.image_small.save(
                        small_image.name,
                        small_image,
                        save=False
                    )
                
                # Save again to update the image fields
                if processed_original or small_image:
                    super().save(update_fields=['image', 'image_small'])
                        
            except Exception as e:
                logger.error(f"Error processing images for product {self.pk}: {e}")
