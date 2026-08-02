import json

from django.test import SimpleTestCase

from apps.common.renderers import EnvelopeJSONRenderer


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class EnvelopeJSONRendererTests(SimpleTestCase):
    def setUp(self):
        self.renderer = EnvelopeJSONRenderer()

    def test_passes_through_already_enveloped_payload(self):
        payload = {"success": True, "message": "ok", "data": {"id": 1}}
        rendered = json.loads(self.renderer.render(payload, renderer_context={}))
        self.assertEqual(rendered, payload)

    def test_wraps_unenveloped_success_payload(self):
        context = {"response": _FakeResponse(200)}
        rendered = json.loads(self.renderer.render({"id": 1}, renderer_context=context))

        self.assertTrue(rendered["success"])
        self.assertEqual(rendered["data"], {"id": 1})

    def test_wraps_unenveloped_failure_payload(self):
        context = {"response": _FakeResponse(404)}
        rendered = json.loads(
            self.renderer.render({"detail": "Not found."}, renderer_context=context)
        )

        self.assertFalse(rendered["success"])
        self.assertEqual(rendered["errors"], {"detail": "Not found."})
