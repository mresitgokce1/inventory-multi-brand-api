"""
Serializers for Category and Product models.
"""
from rest_framework import serializers
from core.constants import ROLE_ADMIN
from accounts.models import Brand
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    """
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'is_active', 
            'brand', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        extra_kwargs = {
            'brand': {'required': False, 'allow_null': True}
        }


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    """
    category_details = CategorySerializer(source='category', read_only=True)
    brand = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'sku', 'description', 'price', 'stock',
            'is_active', 'category', 'category_details', 'brand', 'image', 
            'image_small', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'brand', 'image_small', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        """
        Validate that price is >= 0.
        """
        if value < 0:
            raise serializers.ValidationError("Price must be greater than or equal to 0.")
        return value
    
    def validate_stock(self, value):
        """
        Validate that stock is >= 0.
        """
        if value < 0:
            raise serializers.ValidationError("Stock must be greater than or equal to 0.")
        return value

    def validate_category(self, value):
        """
        Validate that category belongs to the same brand as the product.
        """
        if value is None:
            return value
            
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # For brand managers, ensure category belongs to their brand
            if request.user.role != ROLE_ADMIN and request.user.brand:
                if value.brand != request.user.brand:
                    raise serializers.ValidationError(
                        "Category must belong to your brand."
                    )
            
            # For admin creating a product, ensure category and product brands match
            brand = self.initial_data.get('brand')
            if brand and hasattr(value, 'brand_id'):
                if str(value.brand_id) != str(brand):
                    raise serializers.ValidationError(
                        "Category must belong to the same brand as the product."
                    )
        
        return value


class PublicProductSerializer(serializers.ModelSerializer):
    """
    Serializer for public product listing (limited fields).
    """
    brand = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    image_small_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 
            'image_small_url', 'brand', 'category'
        ]
    
    def get_brand(self, obj):
        """
        Get brand details for public display.
        """
        if obj.brand:
            return {
                'id': obj.brand.id,
                'name': obj.brand.name,
                'slug': obj.brand.slug
            }
        return None
    
    def get_category(self, obj):
        """
        Get category details for public display.
        """
        if obj.category:
            return {
                'id': obj.category.id,
                'name': obj.category.name,
                'slug': obj.category.slug
            }
        return None
    
    def get_image_small_url(self, obj):
        """
        Get the URL for the small image.
        """
        if obj.image_small:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image_small.url)
            return obj.image_small.url
        return None