from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.categories.models import Category


class CategoryModelTests(TestCase):
    def test_str_root_category_returns_name(self):
        root = Category.objects.create(name="Electronics")
        self.assertEqual(str(root), "Electronics")

    def test_str_child_returns_breadcrumb(self):
        root = Category.objects.create(name="Electronics")
        child = Category.objects.create(name="Phones", parent=root)
        self.assertEqual(str(child), "Electronics > Phones")

    def test_is_root_property(self):
        root = Category.objects.create(name="Electronics")
        child = Category.objects.create(name="Phones", parent=root)
        self.assertTrue(root.is_root)
        self.assertFalse(child.is_root)

    def test_slug_auto_generated_and_unique_on_collision(self):
        first = Category.objects.create(name="Books")
        second = Category.objects.create(name="Books", parent=first)
        self.assertEqual(first.slug, "books")
        self.assertNotEqual(second.slug, first.slug)

    def test_duplicate_alive_root_category_name_rejected(self):
        Category.objects.create(name="Electronics")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name="Electronics")

    def test_duplicate_alive_sibling_name_rejected(self):
        root = Category.objects.create(name="Electronics")
        Category.objects.create(name="Phones", parent=root)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Category.objects.create(name="Phones", parent=root)

    def test_same_name_allowed_under_different_parents(self):
        electronics = Category.objects.create(name="Electronics")
        fashion = Category.objects.create(name="Fashion")
        Category.objects.create(name="Phones", parent=electronics)
        # Should not raise
        Category.objects.create(name="Phones", parent=fashion)

    def test_name_reusable_after_soft_delete_root(self):
        first = Category.objects.create(name="Electronics")
        first.delete()
        # Should not raise
        second = Category.objects.create(name="Electronics")
        self.assertNotEqual(first.pk, second.pk)

    def test_name_reusable_after_soft_delete_child(self):
        root = Category.objects.create(name="Electronics")
        first_child = Category.objects.create(name="Phones", parent=root)
        first_child.delete()
        # Should not raise
        second_child = Category.objects.create(name="Phones", parent=root)
        self.assertNotEqual(first_child.pk, second_child.pk)

    def test_soft_delete_default_behavior(self):
        category = Category.objects.create(name="Electronics")
        category.delete()
        category.refresh_from_db()
        self.assertTrue(category.is_deleted)
        self.assertTrue(Category.objects.filter(pk=category.pk).exists())
