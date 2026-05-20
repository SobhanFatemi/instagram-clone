import random
import string

from django.contrib.auth import get_user_model
from django.db import transaction

from profiles.models import Profile

User = get_user_model()


def user_has_field(field_name):
    return any(f.name == field_name for f in User._meta.get_fields())


def generate_unique_username():
    while True:
        candidate = "user_" + "".join(random.choices(string.digits, k=6))
        if not User.objects.filter(username__iexact=candidate).exists():
            return candidate


def build_user_defaults(identifier):
    defaults = {}
    if user_has_field("is_active"):
        defaults["is_active"] = True
    if user_has_field("username"):
        defaults["username"] = generate_unique_username()
    return defaults


@transaction.atomic
def get_or_create_user_for_email(email):
    email = email.lower().strip()
    user, created = User.objects.get_or_create(
        email=email,
        defaults=build_user_defaults(email),
    )
    Profile.objects.get_or_create(user=user, defaults={})
    return user


@transaction.atomic
def get_or_create_user_for_phone_number(phone_number):
    phone_number = phone_number.strip()
    user, created = User.objects.get_or_create(
        phone_number=phone_number,
        defaults=build_user_defaults(phone_number),
    )
    Profile.objects.get_or_create(user=user, defaults={})
    return user
