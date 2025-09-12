from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from core.constants import ROLE_ADMIN
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, PublicProductSerializer
from .permissions import IsAdminOrOwnBrand
from .filters import CategoryFilter, ProductFilter, PublicProductFilter


@extend_schema_view(
    list=extend_schema(
        summary="List categories",
        description="List categories accessible to the authenticated user. Admin users see all categories across all brands, while brand managers see only their own brand's categories.",
        tags=["categories"]
    ),
    create=extend_schema(
        summary="Create a new category",
        description="Create a new category. Admin users can specify any brand, while brand managers automatically create categories for their own brand.",
        tags=["categories"]
    ),
    retrieve=extend_schema(
        summary="Retrieve a category",
        description="Retrieve a specific category by ID (if user has access to it).",
        tags=["categories"]
    ),
    update=extend_schema(
        summary="Update a category",
        description="Update a specific category by ID (if user has access to it).",
        tags=["categories"]
    ),
    partial_update=extend_schema(
        summary="Partially update a category",
        description="Partially update a specific category by ID (if user has access to it).",
        tags=["categories"]
    ),
    destroy=extend_schema(
        summary="Delete a category",
        description="Delete a specific category by ID (if user has access to it).",
        tags=["categories"]
    ),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category model with brand-based queryset filtering.
    - Admin users can see all categories
    - Brand managers can only see categories from their brand
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnBrand]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategoryFilter
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']  # Default ordering

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


@extend_schema_view(
    list=extend_schema(
        summary="List products",
        description="List products accessible to the authenticated user. Admin users see all products across all brands, while brand managers see only their own brand's products. Supports filtering by category, active status, price range, and brand (admin only). Includes search by name and SKU, and ordering by various fields.",
        tags=["products"]
    ),
    create=extend_schema(
        summary="Create a new product",
        description="Create a new product. Admin users can specify any brand, while brand managers automatically create products for their own brand. Price and stock must be non-negative. Category must belong to the same brand as the product.",
        tags=["products"]
    ),
    retrieve=extend_schema(
        summary="Retrieve a product",
        description="Retrieve a specific product by ID (if user has access to it).",
        tags=["products"]
    ),
    update=extend_schema(
        summary="Update a product",
        description="Update a specific product by ID (if user has access to it). Image processing is triggered automatically when images are updated.",
        tags=["products"]
    ),
    partial_update=extend_schema(
        summary="Partially update a product",
        description="Partially update a specific product by ID (if user has access to it). Image processing is triggered automatically when images are updated.",
        tags=["products"]
    ),
    destroy=extend_schema(
        summary="Delete a product",
        description="Delete a specific product by ID (if user has access to it).",
        tags=["products"]
    ),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product model with brand-based queryset filtering.
    - Admin users can see all products
    - Brand managers can only see products from their brand
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwnBrand]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'price', 'created_at', 'stock']
    ordering = ['-created_at']  # Default ordering (most recent first)

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
    
    def get_filterset_kwargs(self):
        """
        Pass request to filterset for brand-aware filtering.
        """
        kwargs = super().get_filterset_kwargs()
        kwargs['request'] = self.request
        return kwargs


@extend_schema_view(
    list=extend_schema(
        summary="Browse public products",
        description="Browse active products without authentication. Public read-only access to product catalog with limited fields. Only returns active products. Supports filtering by brand slug, category ID/slug, and price range. Includes search by name and SKU, and ordering by price or creation date.",
        tags=["public-products"]
    ),
    retrieve=extend_schema(
        summary="Get public product details",
        description="Retrieve details of a specific active product without authentication. Returns limited public fields only.",
        tags=["public-products"]
    ),
)
class PublicProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only ViewSet for Product model.
    - AllowAny permission (no authentication required)
    - Only returns active products
    - Limited serializer with public fields only
    - Public filtering options: brand slug, category id/slug, price range
    """
    serializer_class = PublicProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PublicProductFilter
    search_fields = ['name', 'sku']
    ordering_fields = ['price', 'created_at']
    ordering = ['-created_at']  # Default ordering (most recent first)
    
    def get_queryset(self):
        """
        Return only active products for public access.
        """
        return Product.objects.filter(is_active=True).select_related('brand', 'category')
