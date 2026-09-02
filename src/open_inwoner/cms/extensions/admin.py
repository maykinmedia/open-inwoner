from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.shortcuts import redirect
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from cms.extensions import PageExtensionAdmin
from djangocms_versioning import versionables
from djangocms_versioning.constants import DRAFT, PUBLISHED
from djangocms_versioning.helpers import version_list_url
from djangocms_versioning.models import Version

from .models import CommonExtension

# States that djangocms-versioning refuses to delete, see the `forbidden` check in
# its VersionAdmin.delete_selected. Published content should be unpublished first,
# drafts should be discarded.
PROTECTED_STATES = (PUBLISHED, DRAFT)


class VersionAdmin(admin.ModelAdmin):
    """
    Register the concrete Version model so admin listings of related objects render
    a link to it. Notably the user deletion confirmation, where versions authored by
    the user block the deletion via Version.created_by's PROTECT.

    djangocms-versioning registers only the per-content-type proxy models, leaving
    Version itself unregistered and its entries unlinked. Do not subclass its
    VersionAdmin here: that class assumes a proxy model.
    """

    fields = (
        "grouper_link",
        "content",
        "number",
        "state",
        "created_by",
        "created",
        "modified",
    )
    readonly_fields = fields

    # the changelist is not linked anywhere, but it stays reachable by url and its
    # bulk delete would skip the per-version checks below
    actions = None

    # djangocms-versioning ships admin/djangocms_versioning/change_list.html for its
    # own version admin, and django picks that up here based on the app label. It
    # includes a breadcrumb template that only that admin puts in the context, so
    # rendering it from this admin fails. Use the stock template instead.
    change_list_template = "admin/change_list.html"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # A version cannot be edited here: saving the form would set `state`, which
        # raises because the field is write-protected. Use the actions on the
        # version list to publish, archive or revert a version.
        return False

    def _deletion_error(self, obj):
        """
        Return why `obj` may not be deleted, or None when it may.

        Read the setting rather than djangocms_versioning.conf, which binds it once
        at import time and so never sees a change.
        """
        if not getattr(settings, "DJANGOCMS_VERSIONING_ALLOW_DELETING_VERSIONS", False):
            return _("Deleting versions is disabled.")
        if obj.state in PROTECTED_STATES:
            return _(
                "Draft or published versions cannot be deleted. First unpublish "
                "or use discard for drafts."
            )
        return None

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # hide the delete button for versions that may not be deleted, so nobody is
        # sent to a confirmation page that only refuses
        obj = self.get_object(request, unquote(object_id))
        extra_context = {
            **(extra_context or {}),
            "show_delete": obj is not None and not self._deletion_error(obj),
        }
        return super().change_view(request, object_id, form_url, extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        """
        Refuse to delete published and draft versions, or anything at all when
        DJANGOCMS_VERSIONING_ALLOW_DELETING_VERSIONS is off.

        Deleting a version also deletes its content object, and the page itself when
        it was the last version. Note this cannot be expressed in
        `has_delete_permission`: the deletion confirmation of a related model calls
        it, and a False there replaces the list of blocking versions with a generic
        permissions message.
        """
        obj = self.get_object(request, unquote(object_id))
        error = self._deletion_error(obj) if obj is not None else None
        if error:
            self.message_user(request, error, messages.ERROR)
            return redirect(
                "admin:djangocms_versioning_version_change", object_id=object_id
            )
        return super().delete_view(request, object_id, extra_context)

    @admin.display(description=_("Belongs to"))
    def grouper_link(self, obj):
        """
        Identify the object the version belongs to, e.g. the CMS page.

        The version itself only renders as "Version #<pk>", which says nothing about
        what is being versioned.
        """
        if obj.content is None or not versionables.exists_for_content(obj.content):
            return self.get_empty_value_display()
        return format_html(
            '<a href="{}">{}</a>',
            version_list_url(obj.content),
            obj.grouper,
        )


admin.site.register(Version, VersionAdmin)


class CommonExtensionAdmin(PageExtensionAdmin):
    pass


admin.site.register(CommonExtension, CommonExtensionAdmin)
