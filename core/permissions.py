"""
Custom permissions for brand-scoped access control.
"""
from rest_framework.permissions import BasePermission
from core.constants import ROLE_ADMIN


class IsAdminOrBrandScoped(BasePermission):
    """
    Permission class that allows:
    - Admins: Full access to all resources
    - Brand Managers: Access only to their own brand's resources
    """
    
    def has_permission(self, request, view):
        """
        Check if user has permission to access the view.
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Admin has full access
        if request.user.role == ROLE_ADMIN:
            return True
            
        # Brand Manager must have a brand assigned
        if request.user.brand is None:
            return False
            
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to access the specific object.
        """
        # Admin has full access
        if request.user.role == ROLE_ADMIN:
            return True
            
        # Brand Manager can only access objects from their own brand
        if hasattr(obj, 'brand'):
            return obj.brand == request.user.brand
            
        # If object doesn't have a brand attribute, deny access
        return False