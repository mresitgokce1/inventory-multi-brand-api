from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.utils import timezone
from django.conf import settings
from django.http import Http404
import qrcode
import qrcode.image.svg
import base64
import io
from core.constants import ROLE_ADMIN, ROLE_BRAND_MANAGER
from .models import Category, Product, ProductQRCode
from .serializers import (
    CategorySerializer, ProductSerializer, PublicProductSerializer,
    QRCodeGenerateSerializer, QRCodeResponseSerializer, QRResolveResponseSerializer
)
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
    
    @extend_schema(
        methods=['POST'],
        summary="Generate QR code for product",
        description="Generate a QR code for the product. Creates or returns existing QR code. Supports regeneration to invalidate old codes.",
        request=QRCodeGenerateSerializer,
        responses={200: QRCodeResponseSerializer},
        tags=["products"]
    )
    @action(detail=True, methods=['post'], url_path='qr-code')
    def qr_code(self, request, pk=None):
        """
        Generate QR code for a product.
        """
        product = self.get_object()
        serializer = QRCodeGenerateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        format_type = data.get('format', 'png')
        size = data.get('size', 256)
        regenerate = data.get('regenerate', False)
        
        # Get or create QR code
        qr_code, created = ProductQRCode.objects.get_or_create(product=product)
        
        # Regenerate if requested
        if regenerate and not created:
            # Update regeneration timestamp
            qr_code.regenerated_at = timezone.now()
            # Generate new code
            qr_code.code = ""  # Clear code to force regeneration
            qr_code.save()
        
        # Generate QR image
        frontend_url = f"{settings.FRONTEND_BASE_URL}/p/{qr_code.code}"
        
        if format_type == 'svg':
            # For now, just return PNG with warning - SVG support can be added later
            # TODO: Implement proper SVG support
            format_type = 'png'
        
        # PNG format
        qr = qrcode.QRCode(version=1, box_size=size//25, border=4)
        qr.add_data(frontend_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
        mime_type = 'image/png'
        
        response_data = {
            'code': qr_code.code,
            'url': frontend_url,
            'image_base64': img_base64,
            'mime_type': mime_type
        }
        
        return Response(response_data)


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


class QRResolveView(APIView):
    """
    Resolve QR code and return product information based on authentication.
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Resolve QR code",
        description="Resolve a QR code and return product information. Unauthenticated users get public fields only. Authenticated users from the same brand get private fields too.",
        responses={200: QRResolveResponseSerializer},
        tags=["qr-codes"]
    )
    def get(self, request, code):
        """
        Resolve QR code and return product data based on user authentication and brand.
        """
        try:
            qr_code = ProductQRCode.objects.select_related('product__brand', 'product__category').get(
                code=code, active=True
            )
        except ProductQRCode.DoesNotExist:
            raise Http404("QR code not found")
        
        product = qr_code.product
        
        # Determine visibility level
        if request.user.is_authenticated:
            if request.user.role == ROLE_ADMIN:
                visibility = 'admin'
            elif (request.user.role == ROLE_BRAND_MANAGER and 
                  request.user.brand and 
                  request.user.brand == product.brand):
                visibility = 'manager'
            else:
                visibility = 'public'
        else:
            visibility = 'public'
        
        # Build public product data
        product_public = {
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'price': str(product.price),
            'image_small_url': request.build_absolute_uri(product.image_small.url) if product.image_small else None,
            'description': product.description,
            'brand': {
                'id': product.brand.id,
                'name': product.brand.name,
                'slug': product.brand.slug
            } if product.brand else None,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
                'slug': product.category.slug
            } if product.category else None
        }
        
        # Build response
        response_data = {
            'visibility': visibility,
            'product_public': product_public
        }
        
        # Add private data for authenticated same-brand users or admins
        if visibility in ['manager', 'admin']:
            response_data['product_private'] = {
                'sku': product.sku,
                'stock': product.stock
            }
        
        return Response(response_data)
