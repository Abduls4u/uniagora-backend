from django.test import TestCase

from apps.categories.models import Category
from apps.categories.serializers import (
    CategoryCreateSerializer,
    CategorySerializer,
    CategoryUpdateSerializer,
)


class CategoryCreateSerializerTests(TestCase):
    def test_valid_root_payload(self):
        serializer = CategoryCreateSerializer(data={"name": "Electronics"})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_duplicate_name_under_same_parent_rejected(self):
        root = Category.objects.create(name="Electronics")
        Category.objects.create(name="Phones", parent=root)
        serializer = CategoryCreateSerializer(
            data={"name": "Phones", "parent": root.slug}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_same_name_allowed_under_different_parent(self):
        arts = Category.objects.create(name="Faculty of Arts")
        science = Category.objects.create(name="Faculty of Science")
        Category.objects.create(name="Books", parent=arts)
        serializer = CategoryCreateSerializer(
            data={"name": "Books", "parent": science.slug}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_create_may_reuse_soft_deleted_root_name(self):
        original = Category.objects.create(name="Electronics")
        original.delete()
        serializer = CategoryCreateSerializer(data={"name": "Electronics"})
        self.assertTrue(serializer.is_valid(), serializer.errors)


class CategoryUpdateSerializerTests(TestCase):
    def test_only_name_is_accepted(self):
        category = Category.objects.create(name="Electronics")
        serializer = CategoryUpdateSerializer(
            category, data={"name": "Consumer Electronics"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(set(serializer.validated_data.keys()), {"name"})

    def test_duplicate_sibling_name_rejected_excluding_self(self):
        root = Category.objects.create(name="Electronics")
        phones = Category.objects.create(name="Phones", parent=root)
        Category.objects.create(name="Laptops", parent=root)
        serializer = CategoryUpdateSerializer(
            phones, data={"name": "Laptops"}, partial=True
        )
        self.assertFalse(serializer.is_valid())

    def test_unchanged_name_does_not_conflict_with_self(self):
        category = Category.objects.create(name="Electronics")
        serializer = CategoryUpdateSerializer(
            category, data={"name": "Electronics"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rename_cannot_collide_with_alive_sibling(self):
        root = Category.objects.create(name="Electronics")
        phones = Category.objects.create(name="Phones", parent=root)
        Category.objects.create(name="Laptops", parent=root)
        serializer = CategoryUpdateSerializer(
            phones, data={"name": "Laptops"}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_rename_may_reuse_name_of_soft_deleted_sibling(self):
        root = Category.objects.create(name="Electronics")
        phones = Category.objects.create(name="Phones", parent=root)
        deleted_sibling = Category.objects.create(name="Laptops", parent=root)
        deleted_sibling.delete()
        serializer = CategoryUpdateSerializer(
            phones, data={"name": "Laptops"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)


class CategorySerializerTests(TestCase):
    def test_read_serializer_fields_and_parent_slug(self):
        root = Category.objects.create(name="Electronics")
        child = Category.objects.create(name="Phones", parent=root)
        data = CategorySerializer(child).data
        self.assertEqual(data["parent"], root.slug)
        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "name",
                "slug",
                "parent",
                "display_order",
                "is_active",
                "created_at",
                "updated_at",
            },
        )
