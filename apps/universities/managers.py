from django.db import models

from apps.common.managers import SoftDeleteQuerySet


class UniversityQuerySet(SoftDeleteQuerySet):
    def active(self):
        return self.alive().filter(is_active=True)


class UniversityManager(models.Manager.from_queryset(UniversityQuerySet)):
    pass
