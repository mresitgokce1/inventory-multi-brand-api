"""
Utility functions for the catalog app.
"""
import random
import string


def generate_base62_code(length=8):
    """
    Generate a random Base62 code using alphanumeric characters.
    
    Args:
        length (int): Length of the code to generate (default: 8)
        
    Returns:
        str: Random Base62 code
    """
    # Base62 character set: 0-9, A-Z, a-z
    base62_chars = string.digits + string.ascii_uppercase + string.ascii_lowercase
    return ''.join(random.choices(base62_chars, k=length))


def generate_unique_qr_code(length=8, max_attempts=100):
    """
    Generate a unique QR code that doesn't exist in the database.
    
    Args:
        length (int): Length of the code to generate (default: 8)
        max_attempts (int): Maximum attempts to generate unique code
        
    Returns:
        str: Unique QR code
        
    Raises:
        ValueError: If unable to generate unique code after max_attempts
    """
    # Import here to avoid circular imports
    from .models import ProductQRCode
    
    for _ in range(max_attempts):
        code = generate_base62_code(length)
        if not ProductQRCode.objects.filter(code=code).exists():
            return code
    
    raise ValueError(f"Unable to generate unique QR code after {max_attempts} attempts")