from django.db import migrations

import structlog

logger = structlog.stdlib.get_logger(__name__)

# frozen copies of `OpenklantApphook.__name__` and `OpenklantApphook.page_template`
CONTACT_PAGE_APPHOOK = "OpenklantApphook"
CONTACT_PAGE_TEMPLATE = "cms/contactform/form_outer.html"


def set_contact_page_template(apps, schema_editor):
    """
    Set the contact form template on contact pages, so the contact form plugin
    shows up and becomes editable.
    """
    PageContent = apps.get_model("cms", "PageContent")

    # all versions, so restoring an older one doesn't undo the fix
    updated = (
        PageContent.objects.filter(page__application_urls=CONTACT_PAGE_APPHOOK)
        .exclude(template=CONTACT_PAGE_TEMPLATE)
        .update(template=CONTACT_PAGE_TEMPLATE)
    )
    logger.info("contact_page_template_set", page_contents_updated=updated)


class Migration(migrations.Migration):
    dependencies = [
        ("openklant", "0042_sanitize_prosemirror_link_hrefs"),
        ("cms", "0041_alter_pageurl_unique_together_pageurl_site_and_more"),
    ]

    operations = [
        migrations.RunPython(
            code=set_contact_page_template,
            # the previous templates are unknown
            reverse_code=migrations.RunPython.noop,
        ),
    ]
