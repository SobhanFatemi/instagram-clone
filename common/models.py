from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

    def soft_delete(self):
        return self.update(deleted_at=timezone.now())

    def restore(self):
        return self.update(deleted_at=None)

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted_only(self):
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()


class SoftDeleteModel(TimeStampedModel):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        if self.deleted_at is None:
            self.deleted_at = timezone.now()
            self.save(update_fields=["deleted_at", "updated_at"])

    def restore(self):
        if self.deleted_at is not None:
            self.deleted_at = None
            self.save(update_fields=["deleted_at", "updated_at"])

    def hard_delete(self):
        return super().delete()

    def delete(self, using=None, keep_parents=False):
        self.soft_delete()