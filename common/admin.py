from django.contrib import admin


class TimestampedAdminMixin:
    readonly_fields = ("created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        for field in ("created_at", "updated_at"):
            if field not in readonly:
                readonly.append(field)
        return readonly


class SoftDeleteAdminMixin:
    list_filter = ("deleted_at",)

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if "deleted_at" not in readonly:
            readonly.append("deleted_at")
        return readonly
