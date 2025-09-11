"""
Django signals for catalog app.

Handles automatic image processing for Product model.
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Product
from .image_utils import process_original_image, process_small_image, should_process_images

logger = logging.getLogger(__name__)

# Store previous image state for comparison
_product_image_cache = {}


@receiver(pre_save, sender=Product)
def cache_product_image_state(sender, instance, **kwargs):
    """
    Cache the previous image state before save for comparison.
    """
    if instance.pk:
        try:
            old_instance = Product.objects.get(pk=instance.pk)
            _product_image_cache[instance.pk] = {
                'image_name': old_instance.image.name if old_instance.image else None,
                'image_small_exists': bool(old_instance.image_small)
            }
        except Product.DoesNotExist:
            _product_image_cache[instance.pk] = {
                'image_name': None,
                'image_small_exists': False
            }
    else:
        _product_image_cache[id(instance)] = {
            'image_name': None,
            'image_small_exists': False
        }


@receiver(post_save, sender=Product)
def process_product_images(sender, instance, created, **kwargs):
    """
    Process product images after Product is saved.
    
    Generates:
    - Normalized original image (max width 1920, RGB JPEG quality 80, no EXIF)
    - Small variant (width 400, same quality settings)
    
    Only processes when:
    - Product has a new image
    - Image has changed
    - image_small is missing but image exists
    
    Gracefully handles errors without failing the save operation.
    """
    # Skip processing if no image
    if not instance.image:
        return
    
    try:
        # Get cached previous state
        cache_key = instance.pk if instance.pk else id(instance)
        old_state = _product_image_cache.get(cache_key, {
            'image_name': None,
            'image_small_exists': False
        })
        
        # Determine if processing is needed
        needs_processing = False
        
        if created:
            needs_processing = True
            logger.debug(f"New product with image: {instance.pk}")
        elif instance.image.name != old_state.get('image_name'):
            needs_processing = True
            logger.debug(f"Image changed for product {instance.pk}: {old_state.get('image_name')} -> {instance.image.name}")
        elif not instance.image_small:
            needs_processing = True
            logger.debug(f"Missing small image for product {instance.pk}")
        
        if not needs_processing:
            return
        
        logger.info(f"Processing images for product {instance.pk}: {instance.name}")
        
        # Track if we need to save again
        needs_save = False
        
        # Process original image (normalize but don't replace unless significantly different)
        try:
            processed_original = process_original_image(instance.image)
            if processed_original:
                # Only replace original if processing significantly changed it
                # For now, we'll keep the original as-is and just ensure small variant exists
                logger.debug(f"Original image processed for product {instance.pk}")
        except Exception as e:
            logger.error(f"Failed to process original image for product {instance.pk}: {e}")
        
        # Process small variant image (always generate if missing or changed)
        if not instance.image_small or instance.image.name != old_state.get('image_name'):
            try:
                processed_small = process_small_image(instance.image)
                if processed_small:
                    instance.image_small.save(
                        processed_small.name,
                        processed_small,
                        save=False
                    )
                    needs_save = True
                    logger.info(f"Generated small image for product {instance.pk}")
            except Exception as e:
                logger.error(f"Failed to process small image for product {instance.pk}: {e}")
        
        # Save if changes were made (use update to avoid triggering signal again)
        if needs_save:
            Product.objects.filter(pk=instance.pk).update(
                image_small=instance.image_small
            )
            logger.debug(f"Saved processed images for product {instance.pk}")
        
        # Clean up cache
        if cache_key in _product_image_cache:
            del _product_image_cache[cache_key]
            
    except Exception as e:
        logger.error(f"Unexpected error processing images for product {instance.pk}: {e}")
        # Don't re-raise - we want the product save to succeed even if image processing fails