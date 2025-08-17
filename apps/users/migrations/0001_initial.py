# Generated manually to resolve migration dependency issues

from django.contrib.auth.models import AbstractUser
from django.db import migrations, models
import django.contrib.auth.models
import django.utils.timezone
import apps.users.managers


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="email address")),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "db_table": "users_user",
            },
            managers=[
                ("objects", apps.users.managers.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="phone number")),
                ("date_of_birth", models.DateField(blank=True, null=True, verbose_name="date of birth")),
                ("newsletter_subscription", models.BooleanField(default=False, help_text="Whether the user wants to receive newsletters", verbose_name="newsletter subscription")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=models.CASCADE, related_name="profile", to="users.user")),
            ],
            options={
                "verbose_name": "user profile",
                "verbose_name_plural": "user profiles",
                "db_table": "users_userprofile",
            },
        ),
        migrations.CreateModel(
            name="Address",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(choices=[("shipping", "Shipping"), ("billing", "Billing")], max_length=20, verbose_name="address type")),
                ("first_name", models.CharField(max_length=50, verbose_name="first name")),
                ("last_name", models.CharField(max_length=50, verbose_name="last name")),
                ("company", models.CharField(blank=True, max_length=100, verbose_name="company")),
                ("address_line_1", models.CharField(max_length=255, verbose_name="address line 1")),
                ("address_line_2", models.CharField(blank=True, max_length=255, verbose_name="address line 2")),
                ("city", models.CharField(max_length=100, verbose_name="city")),
                ("state", models.CharField(blank=True, max_length=100, verbose_name="state/province")),
                ("postal_code", models.CharField(max_length=20, verbose_name="postal code")),
                ("country", models.CharField(max_length=2, verbose_name="country")),
                ("phone", models.CharField(blank=True, max_length=20, verbose_name="phone number")),
                ("is_default", models.BooleanField(default=False, verbose_name="default address")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=models.CASCADE, related_name="addresses", to="users.user")),
            ],
            options={
                "verbose_name": "address",
                "verbose_name_plural": "addresses",
                "db_table": "users_address",
            },
        ),
    ]
