import pytest
from django.contrib.auth import get_user_model
from accounts.models import Brand
from core.constants import ROLE_ADMIN, ROLE_BRAND_MANAGER

User = get_user_model()


@pytest.mark.django_db
class TestPermissionsSmoke:
    """Basic permission smoke tests."""

    def setup_method(self):
        """Set up test data."""
        self.brand = Brand.objects.create(name="Test Brand")

    def test_admin_can_create_brand_manager(self):
        """Test that admin user can create brand manager users."""
        # Create admin user
        admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpassword123",
            role=ROLE_ADMIN,
            is_staff=True
        )
        
        # Admin should be able to create brand manager
        brand_manager = User.objects.create_user(
            email="manager@example.com",
            password="managerpassword123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand
        )
        
        assert admin_user.role == ROLE_ADMIN
        assert brand_manager.role == ROLE_BRAND_MANAGER
        assert brand_manager.brand == self.brand
        assert User.objects.count() == 2

    def test_user_model_properties(self):
        """Test User model properties and methods."""
        user = User.objects.create_user(
            email="test@example.com",
            password="testpassword123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand,
            first_name="Test",
            last_name="User"
        )
        
        # Test string representation
        expected_str = f"test@example.com ({user.get_role_display()})"
        assert str(user) == expected_str
        
        # Test USERNAME_FIELD
        assert User.USERNAME_FIELD == 'email'
        assert User.REQUIRED_FIELDS == []
        
        # Test user properties
        assert user.email == "test@example.com"
        assert user.role == ROLE_BRAND_MANAGER
        assert user.brand == self.brand
        assert user.username is None

    def test_brand_user_relationship(self):
        """Test Brand-User relationship."""
        user1 = User.objects.create_user(
            email="user1@example.com",
            password="password123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand
        )
        
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="password123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand
        )
        
        # Test that brand has users
        assert self.brand.users.count() == 2
        assert user1 in self.brand.users.all()
        assert user2 in self.brand.users.all()

    def test_user_without_brand(self):
        """Test user can exist without a brand (e.g., admin users)."""
        admin_user = User.objects.create_user(
            email="admin@example.com",
            password="adminpassword123",
            role=ROLE_ADMIN
        )
        
        assert admin_user.brand is None
        assert admin_user.role == ROLE_ADMIN

    def test_brand_deletion_sets_users_brand_to_null(self):
        """Test that deleting a brand sets user.brand to NULL."""
        user = User.objects.create_user(
            email="user@example.com",
            password="password123",
            role=ROLE_BRAND_MANAGER,
            brand=self.brand
        )
        
        # Delete the brand
        self.brand.delete()
        
        # Refresh user from database
        user.refresh_from_db()
        
        # User's brand should be None due to SET_NULL
        assert user.brand is None