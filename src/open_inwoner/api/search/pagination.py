from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class SearchPagination(PageNumberPagination):
    page_size = 100

    def get_paginated_response(self, data):
        pagination_data = OrderedDict(
            [
                ("count", self.page.paginator.count),
                ("next", self.get_next_link()),
                ("previous", self.get_previous_link()),
            ]
        )

        return Response({**pagination_data, **data})
