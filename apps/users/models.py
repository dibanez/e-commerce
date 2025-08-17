"""
User models for the ecommerce application.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email as the unique identifier.
    """
    email = models.EmailField(
        'email address',
        unique=True,
        help_text='Email address for the user',
    )
    first_name = models.CharField(
        'first name',
        max_length=150,
        blank=True,
    )
    last_name = models.CharField(
        'last name',
        max_length=150,
        blank=True,
    )
    is_staff = models.BooleanField(
        'staff status',
        default=False,
        help_text='Designates whether the user can log into this admin site.',
    )
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text='Designates whether this user should be treated as active. '
                  'Unselect this instead of deleting accounts.',
    )
    date_joined = models.DateTimeField(
        'date joined',
        default=timezone.now,
    )
    
    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'
        db_table = 'users_user'

    def __str__(self) -> str:
        return self.email

    def clean(self) -> None:
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self) -> str:
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()

    def get_short_name(self) -> str:
        """
        Return the short name for the user.
        """
        return self.first_name or self.email


class UserProfile(models.Model):
    """
    Extended user profile for additional information.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    phone = models.CharField(
        'phone number',
        max_length=20,
        blank=True,
    )
    date_of_birth = models.DateField(
        'date of birth',
        null=True,
        blank=True,
    )
    newsletter_subscription = models.BooleanField(
        'newsletter subscription',
        default=False,
        help_text='Whether the user wants to receive newsletters',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'user profile'
        verbose_name_plural = 'user profiles'
        db_table = 'users_userprofile'

    def __str__(self) -> str:
        return f"Profile for {self.user.email}"


class Address(models.Model):
    """
    Address model for shipping and billing addresses.
    """
    ADDRESS_TYPES = (
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
    )
    type = models.CharField(
        'address type',
        max_length=20,
        choices=ADDRESS_TYPES,
    )
    first_name = models.CharField('first name', max_length=50)
    last_name = models.CharField('last name', max_length=50)
    company = models.CharField('company', max_length=100, blank=True)
    address_line_1 = models.CharField('address line 1', max_length=255)
    address_line_2 = models.CharField('address line 2', max_length=255, blank=True)
    city = models.CharField('city', max_length=100)
    state = models.CharField('state/province', max_length=100)
    postal_code = models.CharField('postal code', max_length=20)
    country = models.CharField('country', max_length=2, default='ES')  # ISO 3166-1 alpha-2
    phone = models.CharField('phone', max_length=20, blank=True)
    is_default = models.BooleanField(
        'default address',
        default=False,
        help_text='Whether this is the default address for this type',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'address'
        verbose_name_plural = 'addresses'
        db_table = 'users_address'
        unique_together = [['user', 'type', 'is_default']]
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'type'],
                condition=models.Q(is_default=True),
                name='unique_default_address_per_type'
            )
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name} - {self.city}, {self.country}"

    def save(self, *args, **kwargs) -> None:
        if self.is_default:
            # Ensure only one default address per type for the user
            Address.objects.filter(
                user=self.user, 
                type=self.type, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def full_address(self) -> str:
        """
        Return the full formatted address.
        """
        lines = [self.address_line_1]
        if self.address_line_2:
            lines.append(self.address_line_2)
        lines.append(f"{self.city}, {self.state} {self.postal_code}")
        lines.append(self.country)
        return '\n'.join(lines)