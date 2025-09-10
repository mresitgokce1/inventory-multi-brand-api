from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.constants import ROLE_ADMIN
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
from .permissions import IsAdminOrOwnBrand


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category model with brand-based queryset filtering.
    - Admin users can see all categories
    - Brand managers can only see categories from their brand
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnBrand]

    def get_queryset(self):
        """
        Return queryset filtered by user's brand permissions.
        """
        user = self.request.user
        
        if user.role == ROLE_ADMIN:
            # Admin users can see all categories
            return Category.objects.all()
        else:
            # Brand managers can only see categories from their brand
            if user.brand:
                return Category.objects.filter(brand=user.brand)
            else:
                # If brand manager has no brand, return empty queryset
                return Category.objects.none()


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product model with brand-based queryset filtering.
    - Admin users can see all products
    - Brand managers can only see products from their brand
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnBrand]

    def get_queryset(self):
        """
        Return queryset filtered by user's brand permissions.
        """
        user = self.request.user
        
        if user.role == ROLE_ADMIN:
            # Admin users can see all products
            return Product.objects.select_related('brand', 'category')
        else:
            # Brand managers can only see products from their brand
            if user.brand:
                return Product.objects.filter(brand=user.brand).select_related('brand', 'category')
            else:
                # If brand manager has no brand, return empty queryset
                return Product.objects.none()
