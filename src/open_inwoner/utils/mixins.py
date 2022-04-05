from time import time
from typing import Iterable, Tuple

from django import forms
from django.conf import settings
from django.core.cache import caches
from django.core.exceptions import PermissionDenied
from django.core.paginator import InvalidPage, Page, Paginator
from django.http import Http404, HttpResponse
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext as _

from .export import render_pdf


class ThrottleMixin:
    """
    A very simple throttling implementation with, hopefully, sane defaults.

    You can specifiy the amount of visits (throttle_visits) a view can get,
    for a specific period (in seconds) throttle_period.
    """

    # n visits per period (in seconds)
    throttle_visits = 100
    throttle_period = 60 ** 2  # in seconds
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


class UUIDAdminFirstInOrder:
    def get_fields(self, request, obj):
        fields = super().get_fields(request, obj)

        # Put uuid first in the list
        fields.remove("uuid")
        fields.insert(0, "uuid")
        return fields


class ExportMixin:
    def get_filename(self):
        return f"{self.model.__name__.lower()}_{self.object.uuid}.pdf"

    def render_to_response(self, context, **response_kwargs):
        context["request"] = self.request

        file = render_pdf(
            self.template_name,
            context,
            base_url=self.request.build_absolute_uri(),
            request=self.request,
        )
        filename = self.get_filename()
        context["file"] = file

        response = HttpResponse(file, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response


class FileUploadLimitMixin(object):
    upload_error_messages = {
        "min_size": _(
            "Een aangeleverd bestand dient minimaal %(size)s te zijn, uw bestand is te klein."
        ),
        "max_size": _(
            "Een aangeleverd bestand dient maximaal %(size)s te zijn, uw bestand is te groot."
        ),
        "file_type": _(
            "Het type bestand dat u hebt geüpload is ongeldig. Geldige bestandstypen zijn: docx, pdf, doc, xlsx, xls, jpeg, jpg, png, txt, odt, odf, ods"
        ),
    }

    def _clean_file_field(self, field_name, error_messages=None):
        _error_messages = error_messages or self.upload_error_messages

        min_upload_size = settings.MIN_UPLOAD_SIZE
        max_upload_size = settings.MAX_UPLOAD_SIZE
        file_types = settings.FILE_TYPES

        f = self.cleaned_data[field_name]

        # checking file size limits
        if f and f.size < min_upload_size:
            raise forms.ValidationError(
                _error_messages["min_size"],
                params={"size": filesizeformat(min_upload_size)},
            )
        if f and f.size > max_upload_size:
            raise forms.ValidationError(
                _error_messages["max_size"],
                params={"size": filesizeformat(max_upload_size)},
            )

        # checking file type limits
        upload_file_type = f.content_type.split("/")[1]
        if upload_file_type not in file_types.split(","):
            raise forms.ValidationError(_error_messages["file_type"])

        return f
