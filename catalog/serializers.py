from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from accounts.models import Brand
from core.constants import ROLE_ADMIN
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model with brand scoping logic.
    Admin users can specify brand, brand managers get brand from user.
    """
    
    class Meta:
        model = Category
        fields = ['id', 'brand', 'name', 'slug', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make brand field read-only for non-admin users
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            if user.role != ROLE_ADMIN:
                self.fields['brand'].read_only = True

    def validate(self, data):
        """
        Validate the entire object and set brand for non-admin users.
        """
        user = self.context['request'].user
        
        if user.role != ROLE_ADMIN:
            # Non-admin users: force brand from user
            if not user.brand:
                raise serializers.ValidationError("Brand manager must be associated with a brand.")
            data['brand'] = user.brand
        
        return super().validate(data)

    def create(self, validated_data):
        """
        Create category - brand logic is handled in validate().
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update category with brand logic:
        - Admin users can change brand
        - Brand managers cannot change brand (should be filtered by queryset anyway)
        """
        user = self.context['request'].user
        
        if user.role != ROLE_ADMIN and 'brand' in validated_data:
            # Non-admin users cannot change brand
            validated_data.pop('brand')
        
        return super().update(instance, validated_data)

    def validate_brand(self, value):
        """
        Validate brand field based on user permissions.
        """
        user = self.context['request'].user
        
        # Admin can set any brand
        if user.role == ROLE_ADMIN:
            return value
        
        # Brand managers can only use their own brand
        if user.brand and value != user.brand:
            raise serializers.ValidationError("You can only create categories for your own brand.")
        
        return value


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model with brand scoping logic and validations.
    """
    
    class Meta:
        model = Product
        fields = [
            'id', 'brand', 'category', 'name', 'slug', 'sku', 'description', 
            'price', 'stock', 'is_active', 'image', 'image_small', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'image_small', 'created_at', 'updated_at']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make brand field read-only for non-admin users
        if hasattr(self, 'context') and 'request' in self.context:
            user = self.context['request'].user
            if user.role != ROLE_ADMIN:
                self.fields['brand'].read_only = True

    def validate_price(self, value):
        """Validate that price is not negative."""
        if value < 0:
            raise serializers.ValidationError("Price must be greater than or equal to 0.")
        return value

    def validate_stock(self, value):
        """Validate that stock is not negative."""
        if value < 0:
            raise serializers.ValidationError("Stock must be greater than or equal to 0.")
        return value

    def validate_category(self, value):
        """
        Validate that category belongs to the same brand as the product.
        """
        if value is not None:
            user = self.context['request'].user
            
            # Get the brand that will be used for this product
            if hasattr(self, 'initial_data') and 'brand' in self.initial_data:
                brand_id = self.initial_data['brand']
                try:
                    brand = Brand.objects.get(id=brand_id)
                except Brand.DoesNotExist:
                    raise serializers.ValidationError("Invalid brand specified.")
            else:
                # For brand managers, use their brand
                if user.role != ROLE_ADMIN:
                    brand = user.brand
                else:
                    # For admin updating existing product
                    if self.instance:
                        brand = self.instance.brand
                    else:
                        raise serializers.ValidationError("Brand must be specified.")
            
            if value.brand != brand:
                raise serializers.ValidationError("Category must belong to the same brand as the product.")
        
        return value

    def validate(self, data):
        """
        Validate the entire object and set brand for non-admin users.
        """
        user = self.context['request'].user
        
        if user.role != ROLE_ADMIN:
            # Non-admin users: force brand from user
            if not user.brand:
                raise serializers.ValidationError("Brand manager must be associated with a brand.")
            data['brand'] = user.brand
        
        return super().validate(data)

    def create(self, validated_data):
        """
        Create product - brand logic is handled in validate().
        """
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update product with brand logic:
        - Admin users can change brand
        - Brand managers cannot change brand
        """
        user = self.context['request'].user
        
        if user.role != ROLE_ADMIN and 'brand' in validated_data:
            # Non-admin users cannot change brand
            validated_data.pop('brand')
        
        return super().update(instance, validated_data)

    def validate_brand(self, value):
        """
        Validate brand field based on user permissions.
        """
        user = self.context['request'].user
        
        # Admin can set any brand
        if user.role == ROLE_ADMIN:
            return value
        
        # Brand managers can only use their own brand
        if user.brand and value != user.brand:
            raise serializers.ValidationError("You can only create products for your own brand.")
        
        return value

    def to_representation(self, instance):
        """
        Customize the representation to include category name for easier reading.
        """
        data = super().to_representation(instance)
        if instance.category:
            data['category_name'] = instance.category.name
        return data