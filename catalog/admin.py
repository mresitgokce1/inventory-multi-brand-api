from django.contrib import admin
from .models import Category, Product, ProductQRCode


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'brand', 'name', 'slug', 'is_active', 'created_at']
    list_filter = ['brand', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'brand', 'name', 'sku', 'category', 'price', 'stock', 'is_active']
    list_filter = ['brand', 'category', 'is_active']
    search_fields = ['name', 'sku', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ProductQRCode)
class ProductQRCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'product', 'active', 'created_at', 'regenerated_at']
    list_filter = ['active', 'created_at', 'regenerated_at']
    search_fields = ['code', 'product__name', 'product__brand__name']
    readonly_fields = ['code', 'created_at', 'updated_at', 'regenerated_at']
