from accounts.services.auth_service import is_generated_username


def build_me_response(user):
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": getattr(user, "email", None),
        "phone_number": getattr(user, "phone_number", None),
        "is_active": user.is_active,
        "is_generated_username": is_generated_username(user.username),
    }


def set_user_email(user, email):
    user.email = email.lower().strip()
    user.is_email_verified = True
    user.save(update_fields=["email", "is_email_verified"])
    return user


def set_user_phone_number(user, phone_number):
    user.phone_number = phone_number.strip()
    user.is_phone_verified = True
    user.save(update_fields=["phone_number", "is_phone_verified"])
    return user