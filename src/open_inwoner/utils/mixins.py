from time import time
from typing import Iterable, Tuple

from django.core.cache import caches
from django.core.exceptions import PermissionDenied
from django.core.paginator import InvalidPage, Page, Paginator
from django.http import Http404
from django.utils.translation import gettext as _


class ThrottleMixin:
    """
    A very simple throttling implementation with, hopefully, sane defaults.
    You can specifiy the amount of visits (throttle_visits) a view can get,
    for a specific period (in seconds) throttle_period.
    """

    # n visits per period (in seconds)
    throttle_visits = 100
    throttle_period = 60**2  # in seconds
    throttle_403 = True
    throttle_name = "default"

    # get and options should always be fast. By default
    # do not throttle them.
    throttle_methods = ["post", "put", "patch", "delete", "head", "trace"]

    def get_throttle_cache(self):
        return caches["default"]

    def get_throttle_identifier(self):
        user = getattr(self, "user_cache", self.request.user)
        return str(user.id)

    def create_throttle_key(self):
        """
        :rtype string Use as key to save the last access
        """

        return "throttling_{id}_{throttle_name}_{window}".format(
            id=self.get_throttle_identifier(),
            throttle_name=self.throttle_name,
            window=self.get_throttle_window(),
        )

    def get_throttle_window(self):
        """
        round down to the throttle_period, which is then used to create the key.
        """
        current_time = int(time())
        return current_time - (current_time % self.throttle_period)

    def get_visits_in_window(self):
        cache = self.get_throttle_cache()
        key = self.create_throttle_key()

        initial_visits = 1
        stored = cache.add(key, initial_visits, self.throttle_period)
        if stored:
            visits = initial_visits
        else:
            try:
                visits = cache.incr(key)
            except ValueError:
                visits = initial_visits
        return visits

    def should_be_throttled(self):
        if self.throttle_methods == "all":
            return True
        return self.request.method.lower() in self.throttle_methods

    def dispatch(self, request, *args, **kwargs):
        if self.throttle_403:
            if (
                self.should_be_throttled()
                and self.get_visits_in_window() > self.throttle_visits
            ):
                raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class IPThrottleMixin(ThrottleMixin):
    """
    Same behavior as ThrottleMixin except it limits the amount of tries
    per IP-address a user can access a certain view.
    """

    def get_throttle_identifier(self):
        # REMOTE_ADDR is correctly set in XForwardedForMiddleware
        return str(self.request.META["REMOTE_ADDR"])


class PaginationMixin:
    paginator_class = Paginator
    page_kwarg = "page"
    paginate_by = 10
    paginate_orphans = 0
    allow_empty = True

    def paginate_object_list(
        self, object_list: Iterable, page_size: int = None
    ) -> Tuple[Paginator, Page, Iterable, bool]:
        """copy MultipleObjectMixin.paginate_queryset method"""
        page_size = page_size or self.paginate_by
        paginator = self.paginator_class(
            object_list,
            page_size,
            orphans=self.paginate_orphans,
            allow_empty_first_page=self.allow_empty,
        )
        page_kwarg = self.page_kwarg
        page = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        try:
            page_number = int(page)
        except ValueError:
            if page == "last":
                page_number = paginator.num_pages
            else:
                raise Http404(
                    _("Page is not 'last', nor can it be converted to an int.")
                )
        try:
            page = paginator.page(page_number)
            return paginator, page, page.object_list, page.has_other_pages()
        except InvalidPage as e:
            raise Http404(
                _("Invalid page (%(page_number)s): %(message)s")
                % {"page_number": page_number, "message": str(e)}
            )

    def paginate_with_context(
        self, object_list: Iterable, page_size: int = None
    ) -> dict:
        """
        Paginate objects with ``self.paginate_object_list`` but returns dict
        instead of the tuple. The returned dict has keys which are used in
        MultipleObjectMixin and is ready to be added to the context
        """

        page_size = page_size or self.paginate_by
        paginator, page, object_list, is_paginated = self.paginate_object_list(
            object_list, page_size
        )
        return {
            "paginator": paginator,
            "page_obj": page,
            "object_list": object_list,
            "is_paginated": is_paginated,
        }
