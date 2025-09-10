"""
Image processing utilities for product images.
"""
import logging
import hashlib
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

def process_product_image(original_field_file, slug=None):
    """
    Process product image: resize original to max 1920px width and create small 400px version.
    
    Args:
        original_field_file: Django ImageField file
        slug: Product slug for naming (optional)
    
    Returns:
        tuple: (processed_original_file, small_file) or (None, None) if processing fails
    """
    try:
        # Open the image
        image = Image.open(original_field_file)
        
        # Convert to RGB if necessary (removes alpha channel, handles CMYK, etc.)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        
        # Remove EXIF data by creating a new image
        image = image.copy()
        
        # Process original image (max width 1920px)
        original_processed = process_image_variant(
            image, max_width=1920, quality=80, suffix='original', slug=slug
        )
        
        # Process small image (width 400px)
        small_processed = process_image_variant(
            image, max_width=400, quality=80, suffix='small', slug=slug
        )
        
        return original_processed, small_processed
        
    except Exception as e:
        logger.error(f"Error processing product image: {e}")
        return None, None


def process_image_variant(image, max_width, quality=80, suffix='', slug=None):
    """
    Process an image variant with specified max width.
    
    Args:
        image: PIL Image object
        max_width: Maximum width for the image
        quality: JPEG quality (1-100)
        suffix: Filename suffix
        slug: Product slug for naming
    
    Returns:
        ContentFile or None if processing fails
    """
    try:
        # Calculate new dimensions maintaining aspect ratio
        original_width, original_height = image.size
        
        if original_width <= max_width:
            # No resizing needed
            new_width, new_height = original_width, original_height
        else:
            # Calculate proportional height
            new_width = max_width
            new_height = int((original_height * new_width) / original_width)
        
        # Resize image if needed
        if (new_width, new_height) != (original_width, original_height):
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to bytes buffer as JPEG
        buffer = BytesIO()
        image.save(
            buffer,
            format='JPEG',
            quality=quality,
            progressive=True,
            optimize=True
        )
        buffer.seek(0)
        
        # Generate filename
        filename = generate_image_filename(slug, suffix)
        
        # Create ContentFile
        return ContentFile(buffer.getvalue(), name=filename)
        
    except Exception as e:
        logger.error(f"Error processing image variant {suffix}: {e}")
        return None


def generate_image_filename(slug, suffix='', extension='jpg'):
    """
    Generate a unique image filename with slug and hash.
    
    Args:
        slug: Product slug
        suffix: Filename suffix (e.g., 'small', 'original')
        extension: File extension
    
    Returns:
        str: Generated filename
    """
    # Create a short hash for uniqueness
    hash_input = f"{slug}_{suffix}".encode('utf-8')
    short_hash = hashlib.md5(hash_input).hexdigest()[:8]
    
    if slug and suffix:
        return f"{slug}_{suffix}_{short_hash}.{extension}"
    elif slug:
        return f"{slug}_{short_hash}.{extension}"
    else:
        return f"product_{short_hash}.{extension}"