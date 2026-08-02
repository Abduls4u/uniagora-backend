from django.test import SimpleTestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.common.pagination import StandardResultsSetPagination


class PaginatedResponseShapeTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.paginator = StandardResultsSetPagination()

    def test_paginated_response_is_wrapped_in_success_envelope(self):
        request = Request(self.factory.get("/?page=1"))
        queryset = list(range(25))

        page = self.paginator.paginate_queryset(queryset, request)
        response = self.paginator.get_paginated_response(page)

        self.assertTrue(response.data["success"])
        data = response.data["data"]
        self.assertEqual(data["count"], 25)
        self.assertEqual(data["current_page"], 1)
        self.assertEqual(data["page_size"], 20)
        self.assertEqual(len(data["results"]), 20)
        self.assertIsNotNone(data["next"])
        self.assertIsNone(data["previous"])

    def test_page_size_query_param_is_respected_up_to_max(self):
        request = Request(self.factory.get("/?page_size=5"))
        queryset = list(range(25))

        page = self.paginator.paginate_queryset(queryset, request)
        self.assertEqual(len(page), 5)
