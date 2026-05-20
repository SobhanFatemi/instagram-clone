from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _normalize_phone(self, phone_number):
        if not phone_number:
            return None
        return phone_number.strip()

    def create_user(self, username, password=None, email=None, phone_number=None, **extra_fields):
        if not username:
            raise ValueError("Username is required.")

        if not email and not phone_number:
            raise ValueError("At least one of email or phone_number must be provided.")

        email = self.normalize_email(email) if email else None
        phone_number = self._normalize_phone(phone_number)

        user = self.model(
            username=username,
            email=email,
            phone_number=phone_number,
            **extra_fields,
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, email=None, phone_number=None, **extra_fields):
        if not username:
            raise ValueError("Superuser must have a username.")

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            username=username,
            password=password,
            email=email,
            phone_number=phone_number,
            **extra_fields,
        )
