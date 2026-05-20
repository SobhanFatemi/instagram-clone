from django.contrib.auth import get_user_model
from django.db.models import Count, ExpressionWrapper, FloatField, Q, Value
from django.db.models.functions import Coalesce

from posts.models import Hashtag, Post
from social.models import Block, Follow


User = get_user_model()


def get_hidden_user_ids(user):
    blocked_ids = Block.objects.filter(
        blocker=user
    ).values_list("blocked_id", flat=True)

    blocked_me_ids = Block.objects.filter(
        blocked=user
    ).values_list("blocker_id", flat=True)

    return set(blocked_ids) | set(blocked_me_ids)


def get_following_user_ids(user):
    return list(
        Follow.objects.filter(
            follower=user
        ).values_list("following_id", flat=True)
    )


def get_feed_queryset(user):
    hidden_user_ids = get_hidden_user_ids(user)
    following_ids = get_following_user_ids(user)

    visible_author_ids = set(following_ids) | {user.id}
    visible_author_ids = visible_author_ids - set(hidden_user_ids)

    return (
        Post.objects
        .filter(
            author_id__in=visible_author_ids,
            deleted_at__isnull=True,
        )
        .select_related("author", "author__profile")
        .prefetch_related("media_items")
        .order_by("-created_at")
    )


def get_explore_queryset(user):
    hidden_user_ids = get_hidden_user_ids(user)
    following_ids = get_following_user_ids(user)

    excluded_author_ids = set(hidden_user_ids) | set(following_ids) | {user.id}

    return (
        Post.objects
        .filter(deleted_at__isnull=True)
        .exclude(author_id__in=excluded_author_ids)
        .select_related("author", "author__profile")
        .prefetch_related("media_items")
        .annotate(
            likes_count=Count("likes", distinct=True),
            views_count=Count("view_count", distinct=True),
            followers_count=Count("author__following_relations", distinct=True),
        )
        .annotate(
            score=ExpressionWrapper(
                Coalesce("likes_count", Value(0)) * Value(0.3)
                + Coalesce("views_count", Value(0)) * Value(0.4)
                + Coalesce("followers_count", Value(0)) * Value(0.3),
                output_field=FloatField(),
            )
        )
        .order_by("-score", "-created_at")
    )


def search_users_queryset(user, query):
    hidden_user_ids = get_hidden_user_ids(user)

    return (
        User.objects
        .filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
        .exclude(id__in=hidden_user_ids)
        .exclude(id=user.id)
        .order_by("username")
    )


def search_posts_queryset(user, query):
    hidden_user_ids = get_hidden_user_ids(user)

    return (
        Post.objects
        .filter(
            Q(caption__icontains=query)
            | Q(post_hashtags__hashtag__name__icontains=query),
            deleted_at__isnull=True,
        )
        .exclude(author_id__in=hidden_user_ids)
        .select_related("author", "author__profile")
        .prefetch_related("media_items")
        .distinct()
        .order_by("-created_at")
    )


def search_hashtags_queryset(query):
    return (
        Hashtag.objects
        .filter(name__icontains=query)
        .order_by("name")
    )
