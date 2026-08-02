"""
Generic Cloudinary-backed fields and file-upload validators.

Backend Architecture §10 (Media Strategy):
    "One reusable Cloudinary-backed field/upload path in common/fields.py,
    used identically by: product images, vendor documents, business logos,
    and (future) chat attachments — one validation code path rather than
    per-model reimplementation."

Requires `cloudinary` and `django-cloudinary-storage` in the project's
dependencies; `common` only wraps them, it does not vendor them.
"""

from cloudinary.models import CloudinaryField as _CloudinaryField
from django.core.exceptions import ValidationError

# 8MB comfortably covers product photos, scanned ID cards, and PDF receipts
# without accepting unreasonably large uploads. A single constant used by
# every upload path in the system (Implementation Decision).
MAX_UPLOAD_SIZE_BYTES = 8 * 1024 * 1024

ALLOWED_IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
ALLOWED_DOCUMENT_CONTENT_TYPES = ALLOWED_IMAGE_CONTENT_TYPES | frozenset(
    {"application/pdf"}
)


def validate_upload_size(file_obj) -> None:
    """
    Rejects any upload exceeding `MAX_UPLOAD_SIZE_BYTES`, regardless of
    which app or field triggered it (DDS §7.2: "File validation for uploads
    (size/type) before they reach Cloudinary, via common/fields.py generic
    upload validators").
    """
    size = getattr(file_obj, "size", None)
    if size is not None and size > MAX_UPLOAD_SIZE_BYTES:
        max_mb = MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise ValidationError(f"File too large. Maximum allowed size is {max_mb}MB.")


def validate_image_content_type(file_obj) -> None:
    """Restricts uploads to known image types (product images, store/business logos, university logos)."""
    content_type = getattr(file_obj, "content_type", None)
    if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_CONTENT_TYPES))
        raise ValidationError(
            f"Unsupported image type '{content_type}'. Allowed types: {allowed}."
        )


def validate_document_content_type(file_obj) -> None:
    """Restricts uploads for proof-of-studentship/business documents (image or PDF)."""
    content_type = getattr(file_obj, "content_type", None)
    if content_type and content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES:
        allowed = ", ".join(sorted(ALLOWED_DOCUMENT_CONTENT_TYPES))
        raise ValidationError(
            f"Unsupported document type '{content_type}'. Allowed types: {allowed}."
        )


class CloudinaryImageField(_CloudinaryField):
    """
    Thin, opinionated wrapper around `CloudinaryField` for image uploads.
    Reused verbatim by `ProductImage.image`, `Store`/`VendorProfile`
    logo fields, and `University.logo` — each domain app supplies only a
    `folder`, never re-implements storage wiring or validation.
    """

    def __init__(self, *args, folder: str = "uniagora/images", **kwargs):
        kwargs.setdefault("resource_type", "image")
        kwargs.setdefault("folder", folder)
        super().__init__(*args, **kwargs)


class CloudinaryDocumentField(_CloudinaryField):
    """
    Variant for uploads that are not guaranteed to be images (e.g.
    `VendorDocument.file`, which may be a PDF scan of a school fee
    receipt). `resource_type="auto"` lets Cloudinary detect image vs. raw.
    """

    def __init__(self, *args, folder: str = "uniagora/documents", **kwargs):
        kwargs.setdefault("resource_type", "auto")
        kwargs.setdefault("folder", folder)
        super().__init__(*args, **kwargs)
