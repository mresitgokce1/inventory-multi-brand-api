from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('refresh/', views.refresh_view, name='refresh'),
    path('logout/', views.logout_view, name='logout'),
]