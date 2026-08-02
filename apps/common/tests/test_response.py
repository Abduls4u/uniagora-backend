from django.test import SimpleTestCase

from apps.common.response import error_response, success_response


class SuccessResponseTests(SimpleTestCase):
    def test_default_shape(self):
        response = success_response()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            {"success": True, "message": "", "data": {}},
        )

    def test_carries_data_message_and_status(self):
        response = success_response(data={"id": 1}, message="Created.", status=201)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data,
            {"success": True, "message": "Created.", "data": {"id": 1}},
        )


class ErrorResponseTests(SimpleTestCase):
    def test_default_shape(self):
        response = error_response()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data,
            {"success": False, "message": "", "errors": {}},
        )

    def test_carries_message_and_errors(self):
        response = error_response(
            message="Validation failed.",
            errors={"email": ["This field is required."]},
            status=422,
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.data["success"], False)
        self.assertEqual(response.data["message"], "Validation failed.")
        self.assertEqual(
            response.data["errors"], {"email": ["This field is required."]}
        )
