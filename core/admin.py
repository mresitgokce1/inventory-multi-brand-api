from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category model.
    """
    list_display = ['name', 'brand', 'slug', 'is_active', 'created_at']
    list_filter = ['brand', 'is_active', 'created_at']
    search_fields = ['name', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model.
    """
    list_display = ['name', 'brand', 'category', 'sku', 'price', 'stock', 'is_active']
    list_filter = ['brand', 'category', 'is_active', 'created_at']
    search_fields = ['name', 'sku', 'brand__name', 'category__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['image_small', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('brand', 'category', 'name', 'slug', 'sku')
        }),
        ('Details', {
            'fields': ('description', 'price', 'stock', 'is_active')
        }),
        ('Images', {
            'fields': ('image', 'image_small')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
