from django.test import TestCase

from apps.categories.models import Category


class CategoryManagerTests(TestCase):
    def test_visible_excludes_inactive(self):
        active = Category.objects.create(name="Electronics")
        inactive = Category.objects.create(name="Fashion", is_active=False)
        visible = Category.objects.visible()
        self.assertIn(active, visible)
        self.assertNotIn(inactive, visible)

    def test_visible_excludes_soft_deleted(self):
        category = Category.objects.create(name="Electronics")
        category.delete()
        self.assertNotIn(category, Category.objects.visible())

    def test_alive_includes_inactive(self):
        category = Category.objects.create(name="Fashion", is_active=False)
        self.assertIn(category, Category.objects.alive())
