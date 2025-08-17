"""
Tests for users app.
"""
import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model functionality."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.email == 'test@example.com'
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser
        assert user.check_password('testpass123')

    def test_create_superuser(self):
        """Test creating a superuser."""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='testpass123'
        )
        
        assert admin_user.email == 'admin@example.com'
        assert admin_user.is_active
        assert admin_user.is_staff
        assert admin_user.is_superuser

    def test_user_str_representation(self):
        """Test string representation of user."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        assert str(user) == 'test@example.com'

    def test_user_full_name(self):
        """Test user full name property."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        assert user.get_full_name() == 'John Doe'

    def test_user_short_name(self):
        """Test user short name property."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='John'
        )
        
        assert user.get_short_name() == 'John'

    def test_user_short_name_fallback(self):
        """Test user short name falls back to email."""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        assert user.get_short_name() == 'test@example.com'