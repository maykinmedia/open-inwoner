from typing import Any, Mapping

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template import Context
from django.template.defaultfilters import truncatechars
from django.test import RequestFactory
from django.utils.module_loading import import_string

import structlog
from cms import api
from cms.api import add_plugin
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.models import Page, Placeholder
from cms.page_rendering import render_page
from cms.plugin_rendering import ContentRenderer
from cms.utils.plugins import get_plugins

from open_inwoner.accounts.models import User
from open_inwoner.cms.extensions.models import CommonExtension
from open_inwoner.utils.test import SessionMiddleware

logger = structlog.stdlib.get_logger(__name__)


CMS_TEST_USER_EMAIL = "cms-test-user@example.com"


def _get_or_create_test_user():
    """Get or create a test user for CMS operations that require a user.

    To avoid creating extra users that interfere with tests that check
    User.objects.count(), we prefer using an existing user if available.

    Note: The special email 'cms-test-user@example.com' is used for the
    fallback user. Tests that check user counts should call
    _cleanup_cms_test_user() after CMS setup to remove this user.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()

    # First check if our special CMS test user already exists
    # This ensures we reuse the same user across all CMS operations
    cms_user = User.objects.filter(email=CMS_TEST_USER_EMAIL).first()
    if cms_user:
        return cms_user

    # Prefer using an existing superuser or staff user
    existing_user = User.objects.filter(is_superuser=True).first()
    if existing_user:
        return existing_user

    existing_user = User.objects.filter(is_staff=True).first()
    if existing_user:
        return existing_user

    # Use any existing user if available
    existing_user = User.objects.first()
    if existing_user:
        return existing_user

    # Only create a new user if none exists
    user, _ = User.objects.get_or_create(
        email=CMS_TEST_USER_EMAIL,
        defaults={"first_name": "CMS", "last_name": "Test"},
    )
    return user


def _cleanup_cms_test_user():
    """Mark the CMS test user as inactive to exclude from active user counts.

    Call this at the end of setUpClass after CMS pages are created.
    Tests should use user_queryset() to get a queryset that excludes
    this system user.

    Note: We cannot delete the user because Version.created_by has
    null=False and on_delete=PROTECT.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    User.objects.filter(email=CMS_TEST_USER_EMAIL).update(is_active=False)


def user_queryset():
    """Return a User queryset that excludes the CMS test user.

    Use this in tests instead of User.objects to avoid counting the
    CMS test user that was created for CMS page setup.
    """
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.exclude(email=CMS_TEST_USER_EMAIL)


def _publish_page(page, language="nl"):
    """Publish a CMS page using the versioning API."""
    from django.contrib.contenttypes.models import ContentType

    from djangocms_versioning.constants import DRAFT, PUBLISHED
    from djangocms_versioning.models import Version

    from open_inwoner.cms.utils import get_page_content

    page_content = get_page_content(page, language, include_drafts=True)
    if not page_content:
        return

    content_type = ContentType.objects.get_for_model(page_content)
    user = _get_or_create_test_user()

    # Try to find the version using a direct query (more reliable in tests than get_for_content)
    version = Version.objects.filter(
        content_type=content_type,
        object_id=page_content.pk,
    ).first()

    if version:
        if version.state == DRAFT:
            version.publish(user)
    else:
        # Create a version if none exists (shouldn't happen with created_by param)
        # Use get_or_create to avoid race conditions in TransactionWebTest
        version, created = Version.objects.get_or_create(
            content_type=content_type,
            object_id=page_content.pk,
            defaults={
                "state": PUBLISHED,
                "created_by": user,
            },
        )
        if not created and version.state == DRAFT:
            version.publish(user)


def _unpublish_page(page, language="nl"):
    """Unpublish a CMS page using the versioning API."""
    from django.contrib.contenttypes.models import ContentType

    from djangocms_versioning.constants import PUBLISHED
    from djangocms_versioning.models import Version

    from open_inwoner.cms.utils import get_page_content

    page_content = get_page_content(page, language, include_drafts=True)
    if not page_content:
        return

    content_type = ContentType.objects.get_for_model(page_content)
    user = _get_or_create_test_user()

    # Find the published version
    version = Version.objects.filter(
        content_type=content_type,
        object_id=page_content.pk,
        state=PUBLISHED,
    ).first()

    if version:
        version.unpublish(user)


def create_homepage():
    """
    helper to create an empty, published homepage

    In CMS 4.x with djangocms-versioning, pages are published via the versioning
    system. The api.create_page() creates a draft, and we need to publish it
    using the versioning API.
    """
    user = _get_or_create_test_user()

    p = api.create_page(
        "Home",
        "cms/fullwidth.html",
        "nl",
        in_navigation=True,
        reverse_id="home",
        created_by=user,
    )
    p.set_as_homepage()

    # In CMS 4.x, publish via versioning
    _publish_page(p, "nl")

    return p


def _init_plugin(plugin_class, plugin_data=None) -> tuple[dict, str]:
    if plugin_data is None:
        plugin_data = dict()

    placeholder = Placeholder.objects.create(slot="test")
    model_instance = add_plugin(
        placeholder,
        plugin_class,
        "nl",
        **plugin_data,
    )
    return model_instance


def get_request(
    *,
    user: User | None = None,
    session_vars: Mapping[str, Any] | None = None,
    page: Page | None = None,
):
    request = RequestFactory().get("/")
    if user:
        request.user = user
    else:
        request.user = AnonymousUser()

    if page:
        request.current_page = page

    request.csp_nonce = "test-nonce"

    middleware = SessionMiddleware()
    middleware.process_request(request)
    if session_vars:
        request.session.update(session_vars)
    request.session.save()
    return request


def render_plugin(
    plugin_class,
    plugin_data=None,
    *,
    user=None,
    session_vars=None,
    request_context=None,
) -> tuple[str, dict]:
    model_instance = _init_plugin(plugin_class, plugin_data)
    request = get_request(user=user, session_vars=session_vars)

    context = apply_context_processors(request)

    if request_context:
        context.update(**request_context)

    # note we render twice: once to get the html (to test template tags and parameters etc),
    #   and once to get the returned context (to test returned context content)
    renderer = ContentRenderer(request=request)
    html = renderer.render_plugin(model_instance, context)

    # let's check for output
    if html:
        plugin_instance = model_instance.get_plugin_class_instance()
        context = plugin_instance.render(context, model_instance, None)
    else:
        context = None

    return html, context


def render_all_placeholders(
    page: Page,
    *,
    as_user: User | None = None,
    language: str = "nl",
):
    """Render all placeholders in a CMS page to a single string."""
    from open_inwoner.cms.utils import get_page_placeholders

    logger.info("Rendering all placeholders for CMS page", page=page)
    request = get_request(page=page, user=as_user)
    renderer = ContentRenderer(request=request)

    placeholders = get_page_placeholders(page, language, include_drafts=True)

    if not placeholders.exists():
        logger.info("CMS page has no placeholders to render")
        return ""

    for placeholder in placeholders:
        logger.debug("rendering placeholder", placeholder=placeholder)
        plugins = get_plugins(
            request=request, placeholder=placeholder, template=None, lang=language
        )

        rendered_content_fragments = []
        for plugin_instance in plugins:
            logger.debug("rendering plugin", plugin_instance=plugin_instance)
            rendered_content = renderer.render_plugin(
                instance=plugin_instance,
                context=Context({"request": request}),
                placeholder=placeholder,
            )
            rendered_content_fragments.append(rendered_content)
            logger.debug(
                "rendered content",
                content=truncatechars(rendered_content, 127),
            )

        return "\n".join(rendered_content_fragments)

    return ""


def render_full_page(page: Page, *, as_user: User | None = None):
    """
    Render a full Django CMS page with container template in Django CMS 3.11
    """
    from django.http import HttpResponseRedirect

    request = get_request(user=as_user, page=page)

    # Use the render_page function
    rendered_response = render_page(request, page, current_language="nl", slug=None)

    # Handle redirect responses (e.g., for unpublished pages)
    if isinstance(rendered_response, HttpResponseRedirect):
        return ""

    # Only call render() if the response has a render method (TemplateResponse)
    if hasattr(rendered_response, "render"):
        rendered_response.render()

    content = rendered_response.content
    if isinstance(content, bytes):
        content = content.decode("utf-8")
    return content


def import_context_processors():
    paths = settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
    processors = [import_string(p) for p in paths]
    return processors


def apply_context_processors(request):
    processors = import_context_processors()
    context = {
        "request": request,
    }
    for proc in processors:
        ctx = proc(request)
        if ctx:
            context.update(ctx)
    return context


def create_apphook_page(
    hook_class: type[CMSApp],
    *,
    title=None,
    extension_args: dict = None,
    config_args: dict = None,
    parent_page=None,
    publish=True,
):
    user = _get_or_create_test_user()

    p = api.create_page(
        (title or hook_class.name),
        "cms/fullwidth.html",
        "nl",
        slug=hook_class.app_name,
        apphook=hook_class.__name__,
        apphook_namespace=hook_class.app_name,
        in_navigation=True,
        parent=parent_page,
        created_by=user,
    )
    # create common extension
    if extension_args:
        extension_args["extended_object"] = p
        CommonExtension.objects.create(**extension_args)

    # create app_config
    if app_config := apphook_pool.get_apphook(hook_class.__name__).app_config:
        # attach it to the page for convenience
        if config_args is None:
            config_args = dict()
        config_args["namespace"] = hook_class.app_name
        p.app_config = app_config.objects.get_or_create(**config_args)

    # In CMS 4.x, publish via versioning
    if publish:
        _publish_page(p, "nl")

    return p


def create_cms_page_with_content(
    *, title: str, content: str, language: str = "nl"
) -> Page:
    """Create a CMS page with `content` text in the content slot."""
    from open_inwoner.cms.utils import get_page_placeholder

    user = _get_or_create_test_user()

    page = api.create_page(
        title, "cms/fullwidth.html", language, in_navigation=True, created_by=user
    )

    content_placeholder = get_page_placeholder(
        page, "content", language, include_drafts=True
    )
    if content_placeholder:
        add_plugin(
            placeholder=content_placeholder,
            plugin_type="TextPlugin",
            language=language,
            body=content,
        )

    # In CMS 4.x, publish via versioning
    _publish_page(page, language)

    return page
