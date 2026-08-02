"""
Global renderer enforcing the PRD §17 response envelope as a backstop.

Backend Architecture §9 (API Conventions):
    "enforced globally via a shared renderer + common/exceptions.py custom
    exception handler, so no individual view can break the contract."

In normal operation every response already arrives pre-wrapped via
`response.py` helpers (success paths) or `exceptions.custom_exception_handler`
(failure paths). This renderer is the second, independent line of defense:
if a view or a third-party DRF code path ever emits an unwrapped payload,
it is wrapped here rather than reaching the client malformed.
"""

from typing import Any

from rest_framework.renderers import JSONRenderer


class EnvelopeJSONRenderer(JSONRenderer):
    def render(
        self,
        data: Any,
        accepted_media_type: str | None = None,
        renderer_context: dict | None = None,
    ) -> bytes:
        if isinstance(data, dict) and "success" in data:
            payload = data
        else:
            response = (renderer_context or {}).get("response")
            status_code = getattr(response, "status_code", 200)
            is_success = status_code < 400

            if is_success:
                payload = {
                    "success": True,
                    "message": "",
                    "data": data if data is not None else {},
                }
            else:
                payload = {
                    "success": False,
                    "message": "",
                    "errors": data if data is not None else {},
                }

        return super().render(payload, accepted_media_type, renderer_context)
