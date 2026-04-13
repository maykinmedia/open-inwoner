from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Count, ProtectedError

import structlog
from cms.models import (
    Page,
    PageContent,
    Placeholder,
)
from djangocms_versioning.models import Version
from packaging.version import Version as PgkVersion

logger = structlog.stdlib.get_logger(__name__)


def _get_replacement_page(page):
    """Return the surviving Page for the same node, or None if there is no counterpart.

    In CMS 3 each logical page had two rows (draft + published). After the CMS 4
    migration both survive on the same node_id; the empty one should be deleted and its
    references rerouted to the surviving one. Draft-only pages that were never published
    have no counterpart, so there is nothing to reroute to.
    """
    return Page.objects.filter(node_id=page.node_id).exclude(id=page.id).first()


def _fix_link_plugins(page, replacement_page):
    """djangocms-link with version above 5.0.0 stores only "soft" references to pages in JSON fields which will not be
    updated by `_fix_page_refernces`"""
    if replacement_page is None:
        return

    if "djangocms_link" in settings.INSTALLED_APPS:
        from djangocms_link import __version__
        from djangocms_link.models import Link

        if PgkVersion(__version__) >= PgkVersion("5.0.0"):
            for link in Link.objects.all():
                if "internal_link" in link.link and link.link[
                    "internal_link"
                ].startswith("cms.page:"):
                    _, linked_page_id = link.link["internal_link"].split(":")
                    if linked_page_id == str(page.pk):
                        logger.info(
                            "Fixing link reference",
                            from_page_id=page.id,
                            to_page_id=replacement_page.id,
                        )
                        link.link["internal_link"] = f"cms.page:{replacement_page.pk}"
                        link.save()


def _fix_frontend_refernces(page, replacement_page):
    """djangocms-frontend stores only "soft" references to pages in JSON fields which will not be
    updated by `_fix_page_refernces`"""
    if replacement_page is None:
        return

    def search(json, reference, pk):
        changed = False
        for key, value in json.items():
            if (
                key == "internal_link"
                and isinstance(value, str)
                and value.startswith(reference + ":")
            ):
                # Update link field
                _, linked_page_id = value.split(":")
                if linked_page_id == str(pk):
                    json[key] = f"{reference}:{replacement_page.pk}"
                    changed = True
            elif (
                isinstance(value, dict)
                and "model" in value
                and value["model"] == reference
                and "pk" in value
            ):
                # Update reference
                if value["pk"] == pk:
                    value["pk"] = replacement_page.pk
                    changed = True
            elif isinstance(value, dict):
                # search recursively
                changed = changed or search(value, reference, pk)
        return changed

    if "djangocms_frontend" in settings.INSTALLED_APPS:
        from djangocms_frontend.models import FrontendUIItem

        for frontend_component in FrontendUIItem.objects.all():
            if search(frontend_component.config, "cms.page", page.pk):
                frontend_component.save()


def _fix_page_references(page, replacement_page):
    if replacement_page is None:
        logger.warning(
            "No counterpart page found for Page — skipping reference fix and deleting directly",
            page_id=page.id,
            node_id=page.node_id,
        )
        return

    relations = [
        f
        for f in Page._meta.get_fields()
        if (f.one_to_many or f.one_to_one or f.many_to_many)
        and f.auto_created
        and not f.concrete
    ]

    logger.info(
        "Fixing reference", from_page_id=page.id, to_page_id=replacement_page.id
    )

    for rel in relations:
        model = rel.related_model
        if rel.one_to_one:
            # One to one relationships should not be duplicated, so just delete object
            model.objects.filter(**{rel.field.name: page}).delete()
        elif rel.many_to_many:
            m2m_objs = model.objects.filter(**{rel.field.name: page})
            for m2m_obj in m2m_objs:
                m2m_rel = getattr(m2m_obj, rel.field.name)
                m2m_rel.remove(page)
                m2m_rel.add(replacement_page)
        else:
            model.objects.filter(**{rel.field.name: page}).update(
                **{rel.field.name: replacement_page}
            )

    custom_function = getattr(settings, "CMS_MIGRATION_PROCESS_PAGE_REFERENCES", None)
    if custom_function:
        module, function = custom_function.rsplit(".", 1)
        getattr(
            __import__(module, fromlist=[""]),
            function,
        )(page, replacement_page)


def _delete_page(page):
    try:
        logger.info("Deleting Page", page_id=page.id)
        Page.objects.filter(id=page.id).delete()
    except ProtectedError as err:
        logger.error("Couldn't delete Page", page_id=page.id, error=str(err))


def _delete_page_content_placeholders(page_content_contenttype, page_content):
    placeholders = Placeholder.objects.filter(
        object_id=page_content.pk,
        content_type=page_content_contenttype,
    )
    for placeholder in placeholders:
        try:
            logger.debug(
                "Deleting PageContent Placeholder", placeholder_id=placeholder.id
            )
            placeholder.delete()
        except ProtectedError as err:
            logger.error(
                "Couldn't delete PageContent Placeholder %s %s" % (placeholder.id, err)
            )


def _delete_page_content(page_content):
    try:
        logger.debug("Deleting PageContent", page_content_id=page_content.id)
        page_content.delete()
    except ProtectedError as err:
        logger.error(
            "Couldn't delete PageContent",
            page_content_id=page_content.id,
            error=str(err),
        )


def _get_page_contents(page):
    return PageContent._base_manager.filter(page=page)


def _post_cleanup():
    custom_function = getattr(settings, "CMS_MIGRATION_PROCESS_POST_CLEANUP", None)
    if custom_function:
        module, function = custom_function.rsplit(".", 1)
        getattr(
            __import__(module, fromlist=[""]),
            function,
        )()


class Command(BaseCommand):
    help = "Run after migrations are applied"

    def handle(self, *args, **options):
        page_content_contenttype = ContentType.objects.get(
            app_label="cms", model="pagecontent"
        )
        page_list = Page.objects.all()

        stats = {
            "page_count": page_list.count(),
            "page_deleted": 0,
            "pagecontents_count": 0,
            "pagecontents_deleted": 0,
        }

        for page in page_list:
            # FIXME: An EmptyPageContent type is also deletable!!!

            page_content_list = _get_page_contents(page)

            if not page_content_list.exists():
                replacement_page = _get_replacement_page(page)
                _fix_page_references(page, replacement_page)
                _fix_link_plugins(page, replacement_page)
                _fix_frontend_refernces(page, replacement_page)
                _delete_page(page)
                stats["page_deleted"] = stats["page_deleted"] + 1
                continue

            stats["pagecontents_count"] = (
                stats["pagecontents_count"] + page_content_list.count()
            )

            # Find if each PageContents has versions attached.
            languages = []
            for page_content in page_content_list:
                # If there are no versions for the pagecontents clean them out as they are not required
                if not Version.objects.filter(
                    object_id=page_content.pk,
                    content_type=page_content_contenttype,
                ).count():
                    _delete_page_content_placeholders(
                        page_content_contenttype, page_content
                    )
                    _delete_page_content(page_content)
                    stats["pagecontents_deleted"] = stats["pagecontents_deleted"] + 1
                else:
                    languages.append(page_content.language)

            for language in languages:
                # Delete redundant page urls (the first is the published one - keep it)
                for url in page.urls.filter(language=language).order_by("pk")[1:]:
                    url.delete()

        # Second pass: remove duplicate PageUrls that may have been created when
        # _fix_page_references merged URLs from deleted empty pages into surviving pages.
        # The per-page dedup above runs before the merge happens, so it cannot catch these.
        urls_deleted = 0
        for page in Page.objects.all():
            for lang_entry in (
                page.urls.values("language").annotate(cnt=Count("id")).filter(cnt__gt=1)
            ):
                for url in page.urls.filter(language=lang_entry["language"]).order_by(
                    "pk"
                )[1:]:
                    url.delete()
                    urls_deleted += 1

        if urls_deleted:
            logger.info("Removed duplicate PageUrls", count=urls_deleted)

        _post_cleanup()

        logger.info("Stats", stats=stats)
