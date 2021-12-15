from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class SearchPagination(PageNumberPagination):
    page_size = 12

    def get_paginated_response(self, data):
        pagination_data = OrderedDict(
            [
                ("count", self.page.paginator.count),
                ("next", self.get_next_link()),
                ("previous", self.get_previous_link()),
            ]
        )

        return Response({**pagination_data, **data})

    def get_paginated_response_schema(self, schema):
        pageinate_schema = {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "example": 123,
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://api.example.org/accounts/?{page_query_param}=4".format(
                        page_query_param=self.page_query_param
                    ),
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "example": "http://api.example.org/accounts/?{page_query_param}=2".format(
                        page_query_param=self.page_query_param
                    ),
                },
            },
        }
        return {
            "type": "object",
            "allOf": [
                pageinate_schema,
                schema["items"],
            ],
        }
