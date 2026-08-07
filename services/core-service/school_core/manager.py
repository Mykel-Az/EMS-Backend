from django.db import models
from .tenant import get_current_school_id


class TenantScopedQuerySet(models.QuerySet):
    def for_current_school(self):
        school_id = get_current_school_id()
        if school_id == "ALL":
            return self
        if school_id is None:
            return self.none()  # fail closed, same philosophy as your RLS default
        return self.filter(school=school_id)


class TenantScopedManager(models.Manager):
    def get_queryset(self):
        return TenantScopedQuerySet(self.model, using=self._db).for_current_school()


class TenantScopedModel(models.Model):
    school = models.ForeignKey("school_core.School", on_delete=models.CASCADE, db_index=True)

    objects = TenantScopedManager()

    all_objects = models.Manager()  # This manager will return all objects, regardless of school

    class Meta:
        abstract = True