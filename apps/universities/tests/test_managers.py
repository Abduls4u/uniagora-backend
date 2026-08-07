from django.test import TestCase

from apps.universities.models import University


class UniversityManagerTests(TestCase):
    def setUp(self):
        self.active_alive = University.objects.create(
            name="Active Alive Uni", short_name="AAU"
        )
        self.inactive_alive = University.objects.create(
            name="Inactive Alive Uni", short_name="IAU", is_active=False
        )
        self.active_dead = University.objects.create(
            name="Active Dead Uni", short_name="ADU"
        )
        self.active_dead.delete()

    def test_active_excludes_soft_deleted(self):
        self.assertNotIn(self.active_dead, University.objects.active())

    def test_active_excludes_inactive(self):
        self.assertNotIn(self.inactive_alive, University.objects.active())

    def test_active_includes_active_and_alive(self):
        self.assertIn(self.active_alive, University.objects.active())

    def test_alive_includes_inactive_but_not_deleted(self):
        self.assertIn(self.inactive_alive, University.objects.alive())

    def test_alive_excludes_soft_deleted(self):
        self.assertNotIn(self.active_dead, University.objects.alive())

    def test_dead_returns_only_soft_deleted(self):
        dead_qs = University.objects.dead()
        self.assertIn(self.active_dead, dead_qs)
        self.assertNotIn(self.active_alive, dead_qs)
        self.assertNotIn(self.inactive_alive, dead_qs)
