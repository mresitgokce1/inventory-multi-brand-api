import django_filters
from django_filters import rest_framework as filters
from core.constants import ROLE_ADMIN
from .models import Category, Product


class CategoryFilter(filters.FilterSet):
    """
    FilterSet for Category model with brand-aware filtering.
    """
    name = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    
    class Meta:
        model = Category
        fields = ['is_active']


class ProductFilter(filters.FilterSet):
    """
    FilterSet for Product model with brand-aware filtering.
    Brand filter is only available for admin users.
    """
    category = filters.ModelChoiceFilter(queryset=Category.objects.all())
    is_active = filters.BooleanFilter()
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    brand = filters.ModelChoiceFilter(
        field_name='brand',
        queryset=None,  # Will be set dynamically
        method='filter_brand'
    )
    
    class Meta:
        model = Product
        fields = ['category', 'is_active']
    
    def __init__(self, *args, **kwargs):
        """
        Initialize filter with request context to handle brand filtering.
        """
        super().__init__(*args, **kwargs)
        request = kwargs.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if user.role == ROLE_ADMIN:
                # Admin can filter by any brand
                from accounts.models import Brand
                self.filters['brand'].queryset = Brand.objects.all()
            else:
                # Non-admin users cannot use brand filter
                del self.filters['brand']
            
            # Set category queryset based on user permissions
            if user.role == ROLE_ADMIN:
                self.filters['category'].queryset = Category.objects.all()
            elif user.brand:
                self.filters['category'].queryset = Category.objects.filter(brand=user.brand)
            else:
                self.filters['category'].queryset = Category.objects.none()
    
    def filter_brand(self, queryset, name, value):
        """
        Custom brand filtering method - only available for admin users.
        """
        request = getattr(self, 'request', None)
        if not request or not hasattr(request, 'user'):
            return queryset
        
        user = request.user
        if user.role == ROLE_ADMIN and value:
            return queryset.filter(brand=value)
        
        return queryset


class PublicProductFilter(filters.FilterSet):
    """
    FilterSet for public Product endpoint with limited filtering options.
    Allows filtering by brand slug, category id/slug, price range.
    """
    brand = filters.CharFilter(method='filter_brand_slug', help_text='Filter by brand slug')
    category = filters.CharFilter(method='filter_category_id_or_slug', help_text='Filter by category ID or slug')
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte', help_text='Minimum price filter')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte', help_text='Maximum price filter')
    
    class Meta:
        model = Product
        fields = []  # We handle all filtering through custom methods
    
    def filter_brand_slug(self, queryset, name, value):
        """Filter products by brand slug."""
        if value:
            return queryset.filter(brand__slug=value)
        return queryset
    
    def filter_category_id_or_slug(self, queryset, name, value):
        """Filter products by category ID or slug."""
        if value:
            # Try to filter by ID first (if value is numeric)
            try:
                category_id = int(value)
                return queryset.filter(category_id=category_id)
            except ValueError:
                # If not numeric, filter by slug
                return queryset.filter(category__slug=value)
        return queryset