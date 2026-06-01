from django.core.cache import cache

from .models import Follow


FOLLOWERS_COUNT_KEY = "followers_count:{user_id}"
FOLLOWING_COUNT_KEY = "following_count:{user_id}"
COUNT_CACHE_TTL = 600


def get_followers_count(user):
    key = FOLLOWERS_COUNT_KEY.format(user_id=user.id)
    count = cache.get(key)

    if count is None:
        count = Follow.objects.filter(following=user).count()
        cache.set(key, count, COUNT_CACHE_TTL)

    return count


def get_following_count(user):
    key = FOLLOWING_COUNT_KEY.format(user_id=user.id)
    count = cache.get(key)

    if count is None:
        count = Follow.objects.filter(follower=user).count()
        cache.set(key, count, COUNT_CACHE_TTL)

    return count


def invalidate_follow_counts(*users):
    keys = []

    for user in users:
        keys.append(FOLLOWERS_COUNT_KEY.format(user_id=user.id))
        keys.append(FOLLOWING_COUNT_KEY.format(user_id=user.id))

    cache.delete_many(keys)
