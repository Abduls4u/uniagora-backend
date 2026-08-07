from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.universities.models import University


class UniversityModelTests(TestCase):
    def test_str_returns_short_name(self):
        university = University.objects.create(
            name="University of Ibadan", short_name="UI"
        )
        self.assertEqual(str(university), "UI")

    def test_slug_is_auto_generated_from_name_on_create(self):
        university = University.objects.create(
            name="University of Lagos", short_name="UNILAG"
        )
        self.assertEqual(university.slug, "university-of-lagos")

    def test_slug_is_not_regenerated_on_subsequent_saves(self):
        university = University.objects.create(
            name="Obafemi Awolowo University", short_name="OAU"
        )
        original_slug = university.slug
        university.name = "OAU (Renamed)"
        university.save()
        university.refresh_from_db()
        self.assertEqual(university.slug, original_slug)

    def test_slug_collision_is_deduplicated(self):
        first = University.objects.create(name="Test University!", short_name="TU1")
        second = University.objects.create(name="Test University?", short_name="TU2")
        self.assertEqual(first.slug, "test-university")
        self.assertNotEqual(first.slug, second.slug)
        self.assertTrue(second.slug.startswith("test-university"))

    def test_explicit_slug_is_not_overwritten(self):
        university = University(
            name="Explicit Slug University", short_name="ESU", slug="custom-slug"
        )
        university.save()
        self.assertEqual(university.slug, "custom-slug")

    def test_is_active_defaults_true(self):
        university = University.objects.create(
            name="Default Active Uni", short_name="DAU"
        )
        self.assertTrue(university.is_active)

    def test_name_uniqueness_enforced_at_db_level(self):
        University.objects.create(name="Duplicate Name Uni", short_name="DUP1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                University.objects.create(name="Duplicate Name Uni", short_name="DUP2")

    def test_short_name_uniqueness_enforced_at_db_level(self):
        University.objects.create(name="First Uni", short_name="SAME")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                University.objects.create(name="Second Uni", short_name="SAME")

    def test_soft_delete_sets_is_deleted_and_does_not_remove_row(self):
        university = University.objects.create(name="Soft Delete Uni", short_name="SDU")
        university.delete()
        university.refresh_from_db()
        self.assertTrue(university.is_deleted)
        self.assertTrue(University.objects.filter(pk=university.pk).exists())

    def test_default_manager_is_unfiltered(self):
        """Reference: common app EDD ADR-001 — `objects` must remain
        unfiltered by default; this test locks in that this app has not
        silently reintroduced implicit filtering."""
        university = University.objects.create(name="Unfiltered Uni", short_name="UFU")
        university.delete()
        self.assertIn(university, University.objects.all())
        self.assertNotIn(university, University.objects.alive())

    def test_restore_reverses_soft_delete(self):
        university = University.objects.create(name="Restorable Uni", short_name="RU")
        university.delete()
        university.restore()
        university.refresh_from_db()
        self.assertFalse(university.is_deleted)

    def test_default_ordering_is_alphabetical_by_name(self):
        University.objects.create(name="Zenith University", short_name="ZU")
        University.objects.create(name="Alpha University", short_name="AU")
        names = list(University.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))
