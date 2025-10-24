from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(
            email=email, name=name, phone_number=phone_number, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("name", "Admin")
        extra_fields.setdefault("phone_number", "0000000000")

        # remove from extra_fields to remove duplicates
        name = extra_fields.pop("name")
        phone_number = extra_fields.pop("phone_number")

        return self.create_user(
            email=email,
            password=password,
            name=name,
            phone_number=phone_number,
            **extra_fields
        )


class User(AbstractUser):
    username = None
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True, default="0000000000")
    profile_picture = models.ImageField(
        upload_to="profiles/", default="default.png", null=True
    )
    is_banned = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "phone_number"]

    objects = UserManager()

    def __str__(self):
        return self.email
