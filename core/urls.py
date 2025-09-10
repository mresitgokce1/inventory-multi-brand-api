"""
URL configuration for core app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, public_products_list

app_name = 'core'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    # API endpoints
    path('', include(router.urls)),
    # Public endpoint
    path('public/products/', public_products_list, name='public-products'),
]