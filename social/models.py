from django.conf import settings
from django.db import models
from django.db.models import F, Q

from common.models import TimeStampedModel


class Follow(TimeStampedModel):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relations",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relations",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="unique_follow_relation"),
            models.CheckConstraint(condition=~Q(follower=F("following")), name="prevent_self_follow"),
        ]
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["following"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.follower_id} -> {self.following_id}"


class Block(TimeStampedModel):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocking_relations",
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by_relations",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="unique_block_relation"),
            models.CheckConstraint(condition=~Q(blocker=F("blocked")), name="prevent_self_block"),
        ]
        indexes = [
            models.Index(fields=["blocker"]),
            models.Index(fields=["blocked"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.blocker_id} x {self.blocked_id}"
