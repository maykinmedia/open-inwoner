"""
Programmatic creation of CMS pages.

Used by the setup-configuration bootstrap steps (and by the test helpers in
``open_inwoner.cms.tests.cms_tools``, which wrap these functions with a test
user). Everything in this module runs against production databases, so it must
not create privileged accounts or otherwise rely on test-only assumptions.
"""

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from cms import api
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.models import Page, PageContent, Placeholder
from cms.plugin_base import CMSPluginBase
from djangocms_versioning.constants import DRAFT
from djangocms_versioning.models import Version

from open_inwoner.cms.extensions.models import CommonExtension

# Service account recorded as `Version.created_by` for pages created by
# setup-configuration. It is deliberately inactive and unprivileged: it exists
# only to satisfy the non-nullable FK on the versioning models.
CMS_BOOTSTRAP_USER_EMAIL = "cms-bootstrap@open-inwoner.local"

HOMEPAGE_REVERSE_ID = "home"

DEFAULT_LANGUAGE = "nl"
DEFAULT_TEMPLATE = "cms/fullwidth.html"


def get_cms_bootstrap_user():
    """
    Return the service account used as the author of bootstrapped CMS pages.

    `Version.created_by` is non-nullable and PROTECTed, so publishing requires a
    user. The account cannot log in: it is inactive, has no staff or superuser
    flags, and has an unusable password. Keep it that way; an active account
    here can be adopted by the OIDC backends on an email match.
    """
    UserModel = get_user_model()
    user, created = UserModel.objects.get_or_create(
        email=CMS_BOOTSTRAP_USER_EMAIL,
        defaults={
            "is_active": False,
            "is_staff": False,
            "is_superuser": False,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


@transaction.atomic
def publish_page(page: Page, language: str, *, user) -> None:
    """Publish the draft PageContent version for a CMS 4 page."""
    page_content = PageContent._original_manager.get(page=page, language=language)
    version, _ = Version.objects.get_or_create(
        content_type=ContentType.objects.get_for_model(PageContent),
        object_id=page_content.pk,
        defaults={"created_by": user},
    )
    if version.state == DRAFT:
        version.publish(user)


@transaction.atomic
def update_page_title(
    page: Page, title: str, *, user, language: str = DEFAULT_LANGUAGE
) -> None:
    """
    Overwrite a page's title with `title`.

    A no-op if the title already matches (the draft, if one is in progress,
    otherwise the published one). Overwriting a published title publishes a
    new version, archiving the previous one -- the same as an editor changing
    the title in the admin and publishing.
    """
    content = page.get_admin_content(language)
    if content.title == title:
        return

    version = Version.objects.get_for_content(content)
    if version.state == DRAFT:
        content.title = title
        content.save()
        return

    new_version = version.copy(user)
    new_version.content.title = title
    new_version.content.save()
    new_version.publish(user)


def _get_plugin_instance(placeholder: Placeholder, plugin_class: type[CMSPluginBase]):
    return plugin_class.model.objects.filter(
        placeholder=placeholder, plugin_type=plugin_class.__name__
    ).first()


def _placeholder_for_content(content, slot: str) -> Placeholder | None:
    return Placeholder.objects.filter(
        slot=slot,
        content_type=ContentType.objects.get_for_model(content),
        object_id=content.pk,
    ).first()


def _plugin_needs_sync(
    content, slot: str, plugin_specs: list[tuple[type[CMSPluginBase], dict]]
) -> bool:
    placeholder = _placeholder_for_content(content, slot)
    if placeholder is None:
        return True

    return any(
        (instance := _get_plugin_instance(placeholder, plugin_class)) is None
        or any(getattr(instance, field) != value for field, value in fields.items())
        for plugin_class, fields in plugin_specs
    )


@transaction.atomic
def sync_placeholder_plugins(
    page: Page,
    slot: str,
    plugin_specs: list[tuple[type[CMSPluginBase], dict]],
    *,
    user,
    language: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Ensure each plugin in `plugin_specs` (a list of (plugin class, field
    values) pairs) exists in `page`'s `slot` placeholder, overwriting its
    fields to match. A no-op if nothing needs to change.

    A plugin type not present in `plugin_specs` is left alone, whether it was
    added by an admin or by an earlier run of this step -- the same rule as
    for everything else in the placeholder that this step doesn't explicitly
    manage.
    """
    if not plugin_specs:
        return

    content = page.get_admin_content(language)
    if not _plugin_needs_sync(content, slot, plugin_specs):
        return

    version = Version.objects.get_for_content(content)
    if version.state != DRAFT:
        content = version.copy(user).content

    placeholder, _ = Placeholder.objects.get_or_create(
        slot=slot,
        content_type=ContentType.objects.get_for_model(content),
        object_id=content.pk,
    )
    for plugin_class, fields in plugin_specs:
        instance = _get_plugin_instance(placeholder, plugin_class)
        if instance is None:
            api.add_plugin(placeholder, plugin_class.__name__, language, **fields)
            continue
        for field, value in fields.items():
            setattr(instance, field, value)
        instance.save()

    new_version = Version.objects.get_for_content(content)
    if new_version.state == DRAFT:
        new_version.publish(user)


@transaction.atomic
def create_homepage(
    *,
    user,
    title: str = "Home",
    language: str = DEFAULT_LANGUAGE,
) -> Page:
    """Create an empty, published homepage and set it as the site root."""
    page = api.create_page(
        title,
        DEFAULT_TEMPLATE,
        language,
        in_navigation=True,
        reverse_id=HOMEPAGE_REVERSE_ID,
    )
    page.set_as_homepage()
    publish_page(page, language, user=user)
    return page


@transaction.atomic
def create_apphook_page(
    hook_class: type[CMSApp],
    *,
    user,
    title: str | None = None,
    extension_args: dict | None = None,
    config_args: dict | None = None,
    parent_page: Page | None = None,
    language: str = DEFAULT_LANGUAGE,
    publish: bool = True,
) -> Page:
    """
    Create the CMS page that hosts `hook_class`, with its common extension.

    The page slug is the apphook's `app_name`, so `title` only affects the
    navigation label and the browser tab, never the URL.
    """
    page = api.create_page(
        (title or hook_class.name),
        DEFAULT_TEMPLATE,
        language,
        slug=hook_class.app_name,
        apphook=hook_class.__name__,
        apphook_namespace=hook_class.app_name,
        in_navigation=True,
        parent=parent_page,
    )

    if extension_args:
        CommonExtension.objects.create(extended_object=page, **extension_args)

    _set_app_config_fields(hook_class, config_args)

    if publish:
        publish_page(page, language, user=user)

    return page


def _set_app_config_fields(hook_class: type[CMSApp], config_args: dict | None) -> None:
    """
    Ensure the app config for `hook_class` (e.g. ``ProfileConfig``) exists,
    overwriting its fields with `config_args` if given.

    `namespace` is unique, so it is the only lookup field: an app config from
    an earlier run, or one that predates this page entirely, is reused
    instead of colliding on the unique constraint. The config is created
    (with its model defaults) even when `config_args` is empty, since pages
    for an apphook with a config always have one, whether or not this call
    site has explicit values for it.
    """
    app_config = apphook_pool.get_apphook(hook_class.__name__).app_config
    if not app_config:
        return

    config, _ = app_config.objects.get_or_create(namespace=hook_class.app_name)
    if config_args:
        for field, value in config_args.items():
            setattr(config, field, value)
        config.save()


def get_or_create_homepage(
    *, user, title: str = "Home", language: str = DEFAULT_LANGUAGE
) -> Page:
    """
    Return the site's homepage, creating it if it doesn't exist yet.

    If it does exist, overwrites its title to match `title`.
    """
    page = Page.objects.filter(reverse_id=HOMEPAGE_REVERSE_ID).first()
    if page is None:
        return create_homepage(user=user, title=title, language=language)

    update_page_title(page, title, user=user, language=language)
    return page


def get_or_create_apphook_page(
    hook_class: type[CMSApp],
    *,
    user,
    title: str | None = None,
    extension_args: dict | None = None,
    config_args: dict | None = None,
    parent_page: Page | None = None,
    language: str = DEFAULT_LANGUAGE,
) -> Page:
    """
    Return the page that hosts `hook_class`, creating it if it doesn't exist yet.

    If it does exist, overwrites its title, common extension and app config
    (e.g. ``ProfileConfig``) to match the given values -- the same as an
    editor changing them in the admin, except the change isn't kept.
    """
    page = Page.objects.filter(application_urls=hook_class.__name__).first()
    if page is None:
        return create_apphook_page(
            hook_class,
            user=user,
            title=title,
            extension_args=extension_args,
            config_args=config_args,
            parent_page=parent_page,
            language=language,
        )

    update_page_title(page, title or hook_class.name, user=user, language=language)

    if extension_args:
        extension, _ = CommonExtension.objects.get_or_create(extended_object=page)
        for field, value in extension_args.items():
            setattr(extension, field, value)
        extension.save()

    _set_app_config_fields(hook_class, config_args)

    return page


@transaction.atomic
def _sync_redirect_page_content(
    page: Page,
    *,
    title: str,
    redirect_url: str,
    user,
    language: str = DEFAULT_LANGUAGE,
) -> None:
    """
    Overwrite a redirect page's title and target URL to match, in one version.

    The combined version of `update_page_title`: a redirect page's title and its
    target change together, so doing both in one call means one new version
    (and one publish) instead of two when a re-run changes both.
    """
    content = page.get_admin_content(language)
    if content.title == title and content.redirect == redirect_url:
        return

    version = Version.objects.get_for_content(content)
    if version.state == DRAFT:
        content.title = title
        content.redirect = redirect_url
        content.save()
        return

    new_version = version.copy(user)
    new_version.content.title = title
    new_version.content.redirect = redirect_url
    new_version.content.save()
    new_version.publish(user)


@transaction.atomic
def create_redirect_page(
    *,
    user,
    title: str,
    redirect_url: str,
    reverse_id: str,
    extension_args: dict | None = None,
    parent_page: Page | None = None,
    language: str = DEFAULT_LANGUAGE,
) -> Page:
    """
    Create a plain CMS page with no apphook that redirects to `redirect_url`.

    The sidenav (`SideNavMenuData.get_menu_data`) is built entirely from the CMS
    page tree, so a feature whose content lives at a URL belonging to another app's
    apphook -- rather than one of its own -- needs a page-tree node of its own to get
    a nav entry. This is that node: visiting it sends the browser straight to
    `redirect_url`, via Django CMS's own page-redirect support (`PageContent.redirect`),
    the same mechanism an editor gets by setting a page's "redirect" field in the admin.

    `reverse_id` is this page's lookup key for `get_or_create_redirect_page`, the same
    role `application_urls` plays for an apphook page: there is no apphook to filter
    on, so the caller picks a stable identifier instead.
    """
    page = api.create_page(
        title,
        DEFAULT_TEMPLATE,
        language,
        redirect=redirect_url,
        reverse_id=reverse_id,
        in_navigation=True,
        parent=parent_page,
    )

    if extension_args:
        CommonExtension.objects.create(extended_object=page, **extension_args)

    publish_page(page, language, user=user)
    return page


def get_or_create_redirect_page(
    *,
    user,
    reverse_id: str,
    title: str,
    redirect_url: str,
    extension_args: dict | None = None,
    parent_page: Page | None = None,
    language: str = DEFAULT_LANGUAGE,
) -> Page:
    """
    Return the redirect page identified by `reverse_id`, creating it if needed.

    If it exists, overwrites its title, target URL and common extension to match --
    the same as `get_or_create_apphook_page` does for an apphook page.
    """
    page = Page.objects.filter(reverse_id=reverse_id).first()
    if page is None:
        return create_redirect_page(
            user=user,
            title=title,
            redirect_url=redirect_url,
            reverse_id=reverse_id,
            extension_args=extension_args,
            parent_page=parent_page,
            language=language,
        )

    _sync_redirect_page_content(
        page, title=title, redirect_url=redirect_url, user=user, language=language
    )

    if extension_args:
        extension, _ = CommonExtension.objects.get_or_create(extended_object=page)
        for field, value in extension_args.items():
            setattr(extension, field, value)
        extension.save()

    return page
