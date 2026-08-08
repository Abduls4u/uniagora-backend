from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.universities.models import University
from apps.vendors.models import VendorProfile, VendorStatus, VendorType

User = get_user_model()


class VendorApplyEndpointTests(APITestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Uni of Ibadan", short_name="UI"
        )
        self.user = User.objects.create_user(
            email="student@example.com", password="pass12345", full_name="Student"
        )
        self.url = "/api/v1/vendors/"

    def _payload(self):
        return {
            "university": self.university.pk,
            "vendor_type": VendorType.BUSINESS,
            "store_name": "Store A",
            "phone_number": "+2348012345678",
            "business_name": "Biz",
            "business_address": "Addr",
        }

    def test_requires_authentication(self):
        response = self.client.post(self.url, self._payload())
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_creates_and_returns_verified_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["status"], VendorStatus.VERIFIED)

    def test_conflict_for_existing_profile(self):
        self.client.force_authenticate(self.user)
        self.client.post(self.url, self._payload())
        response = self.client.post(self.url, self._payload())
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @patch("cloudinary.models.CloudinaryField.pre_save")
    def test_student_application_with_document(self, mock_pre_save):
        mock_pre_save.return_value = "test/document.pdf"

        self.client.force_authenticate(self.user)

        payload = {
            "university": self.university.pk,
            "vendor_type": VendorType.STUDENT,
            "store_name": "Store B",
            "phone_number": "+2348012345678",
            "matric_number": "123456",
            "department": "CS",
            "level": "300",
            "document_type": "STUDENT_ID_CARD",
            "document_file": SimpleUploadedFile(
                "id.pdf",
                b"x",
                content_type="application/pdf",
            ),
        }

        response = self.client.post(self.url, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["data"]["documents"]), 1)


class VendorMeEndpointTests(APITestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Uni of Ibadan", short_name="UI"
        )
        self.user = User.objects.create_user(
            email="student@example.com", password="pass12345", full_name="Student"
        )
        self.url = "/api/v1/vendors/me/"

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_404_without_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_returns_own_profile(self):
        VendorProfile.objects.create(
            user=self.user,
            university=self.university,
            vendor_type=VendorType.BUSINESS,
            store_name="Store A",
            phone_number="+2348012345678",
            business_name="Biz",
            business_address="Addr",
        )
        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["store_name"], "Store A")


class VendorAdminEndpointTests(APITestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Uni of Ibadan", short_name="UI"
        )
        self.admin = User.objects.create_user(
            email="admin@example.com",
            password="pass12345",
            full_name="Admin",
            is_staff=True,
        )
        self.customer = User.objects.create_user(
            email="cust@example.com", password="pass12345", full_name="Cust"
        )
        self.vendor_user = User.objects.create_user(
            email="vendor@example.com", password="pass12345", full_name="Vendor"
        )
        self.vendor_profile = VendorProfile.objects.create(
            user=self.vendor_user,
            university=self.university,
            vendor_type=VendorType.BUSINESS,
            store_name="Store A",
            phone_number="+2348012345678",
            business_name="Biz",
            business_address="Addr",
            status=VendorStatus.VERIFIED,
        )
        self.list_url = "/api/v1/vendors/"
        self.suspend_url = f"/api/v1/vendors/{self.vendor_profile.pk}/suspend/"
        self.reinstate_url = f"/api/v1/vendors/{self.vendor_profile.pk}/reinstate/"

    def test_list_requires_admin(self):
        self.client.force_authenticate(self.customer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_returns_profiles_for_admin(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_suspend_requires_admin(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(self.suspend_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_suspend_success_then_conflict_on_repeat(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.suspend_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], VendorStatus.SUSPENDED)

        response = self.client.post(self.suspend_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_reinstate_success_after_suspend(self):
        self.client.force_authenticate(self.admin)
        self.client.post(self.suspend_url)
        response = self.client.post(self.reinstate_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], VendorStatus.VERIFIED)

    def test_reinstate_conflict_when_not_suspended(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.reinstate_url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
