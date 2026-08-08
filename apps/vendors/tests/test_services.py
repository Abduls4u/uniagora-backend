from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.common.exceptions import ConflictError
from apps.universities.models import University
from apps.vendors.models import (
    VendorDocumentStatus,
    VendorProfile,
    VendorStatus,
    VendorType,
)
from apps.vendors.services import (
    VendorApplicationService,
    VendorDocumentService,
    VendorSuspensionService,
    VendorVerificationService,
)

User = get_user_model()


class VendorApplicationServiceTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Uni of Ibadan", short_name="UI"
        )
        self.user = User.objects.create_user(
            email="student@example.com", password="pass12345", full_name="Student One"
        )

    def test_apply_student_creates_profile_document_and_auto_verifies(self):
        vp = VendorApplicationService.apply(
            user=self.user,
            university=self.university,
            vendor_type=VendorType.STUDENT,
            store_name="Store A",
            phone_number="+2348012345678",
            matric_number="123456",
            department="CS",
            level="300",
            document_type="STUDENT_ID_CARD",
            document_file="https://example.com/id.pdf",
        )
        self.assertEqual(vp.status, VendorStatus.VERIFIED)
        self.assertIsNotNone(vp.reviewed_at)
        self.assertIsNone(vp.reviewed_by)
        self.assertEqual(vp.documents.count(), 1)
        self.assertEqual(vp.documents.first().status, VendorDocumentStatus.APPROVED)

    def test_apply_business_creates_profile_without_document_and_auto_verifies(self):
        vp = VendorApplicationService.apply(
            user=self.user,
            university=self.university,
            vendor_type=VendorType.BUSINESS,
            store_name="Store B",
            phone_number="+2348012345678",
            business_name="Biz",
            business_address="Addr",
        )
        self.assertEqual(vp.status, VendorStatus.VERIFIED)
        self.assertEqual(vp.documents.count(), 0)

    def test_apply_second_profile_for_same_user_raises_conflict(self):
        VendorApplicationService.apply(
            user=self.user,
            university=self.university,
            vendor_type=VendorType.BUSINESS,
            store_name="Store B",
            phone_number="+2348012345678",
            business_name="Biz",
            business_address="Addr",
        )
        with self.assertRaises(ConflictError):
            VendorApplicationService.apply(
                user=self.user,
                university=self.university,
                vendor_type=VendorType.BUSINESS,
                store_name="Store C",
                phone_number="+2348012345678",
                business_name="Biz2",
                business_address="Addr2",
            )


class VendorDocumentServiceTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Uni of Ibadan", short_name="UI"
        )
        self.user = User.objects.create_user(
            email="student@example.com", password="pass12345", full_name="Student One"
        )
        self.vendor_profile = VendorProfile.objects.create(
            user=self.user,
            university=self.university,
            vendor_type=VendorType.STUDENT,
            store_name="Store A",
            phone_number="+2348012345678",
            matric_number="123456",
            department="CS",
            level="300",
        )

    def test_second_document_raises_conflict(self):
        VendorDocumentService.create_for_vendor(
            vendor_profile=self.vendor_profile,
            document_type="STUDENT_ID_CARD",
            file="https://example.com/id.pdf",
        )
        with self.assertRaises(ConflictError):
            VendorDocumentService.create_for_vendor(
                vendor_profile=self.vendor_profile,
                document_type="ADMISSION_LETTER",
                file="https://example.com/letter.pdf",
            )


class VendorVerificationServiceTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Uni of Ibadan", short_name="UI"
        )
        self.user = User.objects.create_user(
            email="student@example.com", password="pass12345", full_name="Student One"
        )
        self.vendor_profile = VendorProfile.objects.create(
            user=self.user,
            university=self.university,
            vendor_type=VendorType.STUDENT,
            store_name="Store A",
            phone_number="+2348012345678",
            matric_number="123456",
            department="CS",
            level="300",
        )

    def test_approve_from_pending_succeeds(self):
        vp = VendorVerificationService.approve(vendor_profile=self.vendor_profile)
        self.assertEqual(vp.status, VendorStatus.VERIFIED)

    def test_approve_non_pending_raises_conflict(self):
        VendorVerificationService.approve(vendor_profile=self.vendor_profile)
        with self.assertRaises(ConflictError):
            VendorVerificationService.approve(vendor_profile=self.vendor_profile)

    def test_reject_from_pending_succeeds(self):
        vp = VendorVerificationService.reject(
            vendor_profile=self.vendor_profile, reviewed_by=None
        )
        self.assertEqual(vp.status, VendorStatus.REJECTED)

    def test_reject_non_pending_raises_conflict(self):
        VendorVerificationService.approve(vendor_profile=self.vendor_profile)
        with self.assertRaises(ConflictError):
            VendorVerificationService.reject(
                vendor_profile=self.vendor_profile, reviewed_by=None
            )


class VendorSuspensionServiceTests(TestCase):
    def setUp(self):
        self.university = University.objects.create(
            name="Uni of Ibadan", short_name="UI"
        )
        self.user = User.objects.create_user(
            email="student@example.com", password="pass12345", full_name="Student One"
        )
        self.vendor_profile = VendorProfile.objects.create(
            user=self.user,
            university=self.university,
            vendor_type=VendorType.STUDENT,
            store_name="Store A",
            phone_number="+2348012345678",
            matric_number="123456",
            department="CS",
            level="300",
            status=VendorStatus.VERIFIED,
        )

    def test_suspend_from_verified_succeeds(self):
        vp = VendorSuspensionService.suspend(vendor_profile=self.vendor_profile)
        self.assertEqual(vp.status, VendorStatus.SUSPENDED)

    def test_suspend_non_verified_raises_conflict(self):
        self.vendor_profile.status = VendorStatus.PENDING
        self.vendor_profile.save(update_fields=["status"])
        with self.assertRaises(ConflictError):
            VendorSuspensionService.suspend(vendor_profile=self.vendor_profile)

    def test_reinstate_from_suspended_succeeds(self):
        VendorSuspensionService.suspend(vendor_profile=self.vendor_profile)
        vp = VendorSuspensionService.reinstate(vendor_profile=self.vendor_profile)
        self.assertEqual(vp.status, VendorStatus.VERIFIED)

    def test_reinstate_non_suspended_raises_conflict(self):
        with self.assertRaises(ConflictError):
            VendorSuspensionService.reinstate(vendor_profile=self.vendor_profile)
