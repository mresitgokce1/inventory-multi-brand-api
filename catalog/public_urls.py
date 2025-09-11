from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for public endpoints
public_router = DefaultRouter()
public_router.register(r'products', views.PublicProductViewSet, basename='public-product')

urlpatterns = [
    path('', include(public_router.urls)),
]