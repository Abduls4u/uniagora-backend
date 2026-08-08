from django.test import TestCase

from apps.categories.services import CategoryService
from apps.common.exceptions import ConflictError


class CategoryServiceTests(TestCase):
    def test_create_root_category(self):
        category = CategoryService.create(name="Electronics")
        self.assertIsNone(category.parent)
        self.assertTrue(category.is_active)

    def test_create_child_category(self):
        root = CategoryService.create(name="Electronics")
        child = CategoryService.create(name="Phones", parent=root, display_order=1)
        self.assertEqual(child.parent, root)
        self.assertEqual(child.display_order, 1)

    def test_update_changes_only_name(self):
        category = CategoryService.create(name="Electronics")
        original_slug = category.slug
        updated = CategoryService.update(category=category, name="Consumer Electronics")
        self.assertEqual(updated.name, "Consumer Electronics")
        self.assertEqual(updated.slug, original_slug)

    def test_update_with_no_args_is_a_noop(self):
        category = CategoryService.create(name="Electronics")
        updated = CategoryService.update(category=category)
        self.assertEqual(updated.name, "Electronics")

    def test_activate_conflict_when_already_active(self):
        category = CategoryService.create(name="Electronics")
        with self.assertRaises(ConflictError):
            CategoryService.activate(category=category)

    def test_deactivate_then_activate(self):
        category = CategoryService.create(name="Electronics")
        CategoryService.deactivate(category=category)
        category.refresh_from_db()
        self.assertFalse(category.is_active)
        CategoryService.activate(category=category)
        category.refresh_from_db()
        self.assertTrue(category.is_active)

    def test_deactivate_conflict_when_already_inactive(self):
        category = CategoryService.create(name="Electronics")
        CategoryService.deactivate(category=category)
        with self.assertRaises(ConflictError):
            CategoryService.deactivate(category=category)

    def test_delete_blocked_by_active_child(self):
        root = CategoryService.create(name="Electronics")
        CategoryService.create(name="Phones", parent=root)

        with self.assertRaises(ConflictError):
            CategoryService.delete(category=root)

    def test_delete_blocked_by_inactive_but_alive_child(self):
        root = CategoryService.create(name="Electronics")
        child = CategoryService.create(name="Phones", parent=root)

        CategoryService.deactivate(category=child)

        with self.assertRaises(ConflictError):
            CategoryService.delete(category=root)

    def test_delete_allowed_after_soft_deleting_children(self):
        root = CategoryService.create(name="Electronics")
        child = CategoryService.create(name="Phones", parent=root)

        CategoryService.delete(category=child)
        CategoryService.delete(category=root)

        root.refresh_from_db()
        self.assertTrue(root.is_deleted)

    def test_delete_allowed_with_no_children(self):
        category = CategoryService.create(name="Electronics")

        CategoryService.delete(category=category)

        category.refresh_from_db()
        self.assertTrue(category.is_deleted)
