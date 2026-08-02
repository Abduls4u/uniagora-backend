from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.common.fields import (
    MAX_UPLOAD_SIZE_BYTES,
    validate_document_content_type,
    validate_image_content_type,
    validate_upload_size,
)


@dataclass
class _FakeUploadedFile:
    size: int = 1024
    content_type: str = "image/jpeg"


class ValidateUploadSizeTests(SimpleTestCase):
    def test_accepts_file_within_limit(self):
        validate_upload_size(_FakeUploadedFile(size=1024))  # should not raise

    def test_rejects_file_over_limit(self):
        with self.assertRaises(ValidationError):
            validate_upload_size(_FakeUploadedFile(size=MAX_UPLOAD_SIZE_BYTES + 1))


class ValidateImageContentTypeTests(SimpleTestCase):
    def test_accepts_allowed_image_types(self):
        for content_type in ["image/jpeg", "image/png", "image/webp"]:
            validate_image_content_type(_FakeUploadedFile(content_type=content_type))

    def test_rejects_disallowed_type(self):
        with self.assertRaises(ValidationError):
            validate_image_content_type(
                _FakeUploadedFile(content_type="application/zip")
            )


class ValidateDocumentContentTypeTests(SimpleTestCase):
    def test_accepts_pdf_for_documents(self):
        validate_document_content_type(
            _FakeUploadedFile(content_type="application/pdf")
        )

    def test_rejects_disallowed_type(self):
        with self.assertRaises(ValidationError):
            validate_document_content_type(
                _FakeUploadedFile(content_type="application/zip")
            )
