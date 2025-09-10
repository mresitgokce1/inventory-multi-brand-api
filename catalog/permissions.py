from rest_framework import permissions
from core.constants import ROLE_ADMIN


class IsAdminOrOwnBrand(permissions.BasePermission):
    """
    Custom permission to allow:
    - Admin users: Full access to all objects
    - Brand managers: Access only to objects from their own brand
    """
    
    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
        All authenticated users can access the view.
        """
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access the specific object.
        - Admin users can access any object
        - Brand managers can only access objects from their brand
        """
        # Admin users have full access
        if request.user.role == ROLE_ADMIN:
            return True
        
        # Brand managers can only access objects from their own brand
        if hasattr(obj, 'brand') and request.user.brand:
            return obj.brand == request.user.brand
        
        return False