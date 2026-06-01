from django.core.cache import cache


LOGIN_RATE_LIMIT = 10
LOGIN_RATE_WINDOW_SECONDS = 300

SIGNUP_RATE_LIMIT = 5
SIGNUP_RATE_WINDOW_SECONDS = 3600


class RateLimitError(Exception):
    pass


def hit_rate_limit(key, limit, window):
    cache.add(key, 0, timeout=window)

    try:
        current = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        current = 1

    if current > limit:
        raise RateLimitError("Too many requests. Please try again later.")


def check_login_rate_limit(identifier):
    hit_rate_limit(
        f"login_rate_limit:{identifier}",
        LOGIN_RATE_LIMIT,
        LOGIN_RATE_WINDOW_SECONDS,
    )


def check_signup_rate_limit(identifier):
    hit_rate_limit(
        f"signup_rate_limit:{identifier}",
        SIGNUP_RATE_LIMIT,
        SIGNUP_RATE_WINDOW_SECONDS,
    )
