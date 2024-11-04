from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email_or_phone, password=None, **extra_fields):
        if not email_or_phone:
            raise ValueError("The Email or Phone field must be set")
        user = self.model(email_or_phone=email_or_phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email_or_phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email_or_phone, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    email_or_phone = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=128)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True)
    age = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        validators=[MinValueValidator(16), MaxValueValidator(50)]
    )
    height = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        validators=[MinValueValidator(140), MaxValueValidator(220)]
    )
    weight = models.PositiveIntegerField(
        blank=True, 
        null=True, 
        validators=[MinValueValidator(30), MaxValueValidator(200)]
    )
    goal = models.CharField(max_length=255, blank=True, null=True)
    level = models.CharField(max_length=50, blank=True, null=True)
    is_premium = models.BooleanField(default=False)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # Related names for groups and permissions
    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email_or_phone'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email_or_phone
