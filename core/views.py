from django.shortcuts import render

"""
Views and ViewSets for Category and Product models.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.db.models import Q
from core.constants import ROLE_ADMIN
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer, PublicProductSerializer
from .permissions import IsAdminOrBrandScoped


@extend_schema_view(
    list=extend_schema(tags=['categories']),
    create=extend_schema(tags=['categories']),
    retrieve=extend_schema(tags=['categories']),
    update=extend_schema(tags=['categories']),
    partial_update=extend_schema(tags=['categories']),
    destroy=extend_schema(tags=['categories']),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD operations with brand-scoped access.
    """
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrBrandScoped]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """
        Return categories based on user role and brand.
        """
        queryset = Category.objects.all()
        
        # Admin sees all categories
        if self.request.user.role == ROLE_ADMIN:
            pass  # Return all
        else:
            # Brand Manager sees only their brand's categories
            if self.request.user.brand:
                queryset = queryset.filter(brand=self.request.user.brand)
            else:
                queryset = queryset.none()
        
        # Apply basic filtering
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1']
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Apply search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Set brand for Brand Managers automatically.
        """
        if self.request.user.role != ROLE_ADMIN:
            # Brand Manager: auto-set their brand
            serializer.save(brand=self.request.user.brand)
        else:
            # Admin: must provide brand explicitly
            if 'brand' not in serializer.validated_data or not serializer.validated_data['brand']:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'brand': 'This field is required for admin users.'})
            serializer.save()


@extend_schema_view(
    list=extend_schema(tags=['products']),
    create=extend_schema(tags=['products']),
    retrieve=extend_schema(tags=['products']),
    update=extend_schema(tags=['products']),
    partial_update=extend_schema(tags=['products']),
    destroy=extend_schema(tags=['products']),
)
class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations with brand-scoped access.
    """
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrBrandScoped]
    search_fields = ['name', 'sku']
    ordering_fields = ['name', 'price', 'created_at', 'stock']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return products based on user role and brand.
        """
        queryset = Product.objects.select_related('brand', 'category').all()
        
        # Admin sees all products
        if self.request.user.role == ROLE_ADMIN:
            # Admin can filter by brand
            brand = self.request.query_params.get('brand')
            if brand:
                queryset = queryset.filter(brand_id=brand)
        else:
            # Brand Manager sees only their brand's products
            if self.request.user.brand:
                queryset = queryset.filter(brand=self.request.user.brand)
            else:
                queryset = queryset.none()
        
        # Apply basic filtering
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1']
            queryset = queryset.filter(is_active=is_active_bool)
        
        min_price = self.request.query_params.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        max_price = self.request.query_params.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Apply search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Set brand for Brand Managers automatically.
        """
        if self.request.user.role != ROLE_ADMIN:
            # Brand Manager: auto-set their brand
            serializer.save(brand=self.request.user.brand)
        else:
            # Admin: must provide brand explicitly via POST data
            brand_id = self.request.data.get('brand')
            if not brand_id:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'brand': 'This field is required for admin users.'})
            
            try:
                from accounts.models import Brand
                brand = Brand.objects.get(id=brand_id)
                serializer.save(brand=brand)
            except Brand.DoesNotExist:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({'brand': 'Invalid brand ID.'})


@extend_schema(
    tags=['public-products'],
    description="Public read-only endpoint for active products with filtering and search capabilities."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def public_products_list(request):
    """
    Public read-only endpoint for active products.
    
    Supports filtering by:
    - brand (slug): Filter by brand slug
    - category (id or slug): Filter by category
    - min_price: Filter by minimum price
    - max_price: Filter by maximum price
    - search: Search in product name and SKU
    - ordering: price, -price, created_at, -created_at
    """
    # Start with active products only
    queryset = Product.objects.filter(is_active=True).select_related('brand', 'category')
    
    # Apply filtering
    brand = request.query_params.get('brand')
    if brand:
        queryset = queryset.filter(brand__slug=brand)
    
    category = request.query_params.get('category')
    if category:
        # Try to filter by category ID first, then by slug
        try:
            queryset = queryset.filter(category_id=int(category))
        except (ValueError, TypeError):
            queryset = queryset.filter(category__slug=category)
    
    min_price = request.query_params.get('min_price')
    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    max_price = request.query_params.get('max_price')
    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Apply search
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) | Q(sku__icontains=search)
        )
    
    # Apply ordering
    ordering = request.query_params.get('ordering', '-created_at')
    valid_ordering = ['price', '-price', 'created_at', '-created_at']
    if ordering in valid_ordering:
        queryset = queryset.order_by(ordering)
    else:
        queryset = queryset.order_by('-created_at')
    
    # Apply pagination manually since we're not using a viewset
    from rest_framework.pagination import PageNumberPagination
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    if page is not None:
        serializer = PublicProductSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    serializer = PublicProductSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)
