"""
Image processing utilities for Product images.

Provides functions to process product images into:
- Normalized original: max width 1920, maintain aspect, RGB JPEG quality 80, strip EXIF
- Small variant: width 400 (contain/fit), same quality settings
"""

import logging
from io import BytesIO
from PIL import Image, ExifTags
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Image processing settings
ORIGINAL_MAX_WIDTH = 1920
SMALL_WIDTH = 400
JPEG_QUALITY = 80
JPEG_FORMAT = 'JPEG'


def strip_exif(image):
    """
    Strip EXIF data from an image while preserving orientation.
    
    Args:
        image (PIL.Image): The PIL Image object
        
    Returns:
        PIL.Image: Image with EXIF data stripped
    """
    try:
        # Handle image orientation before stripping EXIF
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        
        if hasattr(image, '_getexif'):
            exif = image._getexif()
            if exif is not None:
                orientation_value = exif.get(orientation)
                if orientation_value:
                    if orientation_value == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation_value == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation_value == 8:
                        image = image.rotate(90, expand=True)
        
        # Create new image without EXIF data
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        return image_without_exif
        
    except Exception as e:
        logger.warning(f"Failed to strip EXIF data: {e}")
        return image


def normalize_image(image, max_width, quality=JPEG_QUALITY):
    """
    Normalize image: resize if needed, convert to RGB, apply quality settings.
    
    Args:
        image (PIL.Image): The PIL Image object
        max_width (int): Maximum width in pixels
        quality (int): JPEG quality (1-100)
        
    Returns:
        PIL.Image: Normalized image
    """
    # Convert to RGB if needed (handles RGBA, P, etc.)
    if image.mode != 'RGB':
        # If image has transparency, composite over white background
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if len(image.split()) > 3 else None)
            image = background
        else:
            image = image.convert('RGB')
    
    # Resize if image is wider than max_width, maintaining aspect ratio
    if image.width > max_width:
        aspect_ratio = image.height / image.width
        new_height = int(max_width * aspect_ratio)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
    
    return image


def process_image_to_file(image, filename_prefix, quality=JPEG_QUALITY):
    """
    Process PIL Image and return Django ContentFile.
    
    Args:
        image (PIL.Image): The PIL Image object
        filename_prefix (str): Prefix for the generated filename
        quality (int): JPEG quality (1-100)
        
    Returns:
        ContentFile: Django ContentFile ready for ImageField
    """
    # Save to BytesIO buffer
    buffer = BytesIO()
    image.save(buffer, format=JPEG_FORMAT, quality=quality, optimize=True)
    buffer.seek(0)
    
    # Generate filename with .jpg extension
    filename = f"{filename_prefix}.jpg"
    
    return ContentFile(buffer.read(), name=filename)


def process_original_image(image_file):
    """
    Process original image: normalize to max width 1920, RGB, JPEG quality 80, strip EXIF.
    
    Args:
        image_file: Django ImageField file
        
    Returns:
        ContentFile or None: Processed image file or None if processing failed
    """
    try:
        # Open and process image
        with Image.open(image_file) as img:
            # Strip EXIF data
            img = strip_exif(img)
            
            # Normalize image
            img = normalize_image(img, ORIGINAL_MAX_WIDTH, JPEG_QUALITY)
            
            # Generate filename without extension (will be added as .jpg)
            filename_base = image_file.name.rsplit('.', 1)[0] if '.' in image_file.name else image_file.name
            filename_prefix = f"{filename_base}_processed"
            
            return process_image_to_file(img, filename_prefix, JPEG_QUALITY)
            
    except Exception as e:
        logger.error(f"Failed to process original image '{image_file.name}': {e}")
        return None


def process_small_image(image_file):
    """
    Process small variant: width 400 (fit), RGB, JPEG quality 80, strip EXIF.
    
    Args:
        image_file: Django ImageField file
        
    Returns:
        ContentFile or None: Processed small image file or None if processing failed
    """
    try:
        # Open and process image
        with Image.open(image_file) as img:
            # Strip EXIF data
            img = strip_exif(img)
            
            # Normalize image to small width
            img = normalize_image(img, SMALL_WIDTH, JPEG_QUALITY)
            
            # Generate filename without extension (will be added as .jpg)
            filename_base = image_file.name.rsplit('.', 1)[0] if '.' in image_file.name else image_file.name
            filename_prefix = f"{filename_base}_small"
            
            return process_image_to_file(img, filename_prefix, JPEG_QUALITY)
            
    except Exception as e:
        logger.error(f"Failed to process small image '{image_file.name}': {e}")
        return None


def should_process_images(instance, old_image=None):
    """
    Determine if images should be processed based on changes.
    
    Args:
        instance: Product instance
        old_image: Previous image file (if any)
        
    Returns:
        bool: True if images should be processed
    """
    # Process if there's a new image
    if instance.image and not old_image:
        return True
    
    # Process if image has changed
    if instance.image and old_image and instance.image.name != old_image.name:
        return True
    
    # Process if image_small is missing but image exists
    if instance.image and not instance.image_small:
        return True
    
    return False