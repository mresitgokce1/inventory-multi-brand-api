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