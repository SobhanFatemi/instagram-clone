def build_me_response(user):
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": getattr(user, "email", None),
        "phone_number": getattr(user, "phone_number", None),
        "is_active": user.is_active,
    }