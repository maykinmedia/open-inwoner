import logging
from typing import Any, Mapping

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.template import Context
from django.test import RequestFactory
from django.utils.module_loading import import_string

from cms import api
from cms.api import add_plugin
from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from cms.models import Placeholder
from cms.plugin_rendering import ContentRenderer
from cms.utils.plugins import get_plugins

from open_inwoner.cms.extensions.models import CommonExtension
from open_inwoner.utils.test import SessionMiddleware

logger = logging.getLogger(__name__)


def create_homepage():
    """
    helper to create an empty, published homepage
    """
    p = api.create_page(
        "Home", "cms/fullwidth.html", "nl", in_navigation=True, reverse_id="home"
    )
    p.set_as_homepage()

    if not p.publish("nl"):
        raise Exception("failed to publish page")

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
    logger.info("Rendering all placeholders for page: %s", page)
    request = get_request(page=page, user=as_user)
    renderer = ContentRenderer(request=request)

    placeholders = page.placeholders.all()

    if not placeholders.exists():
        logger.info("Page has no placeholders to render")
        return ""

    for placeholder in placeholders:
        logger.debug("rendering placeholder: %s", placeholder)
        plugins = get_plugins(
            request=request, placeholder=placeholder, template=None, lang=language
        )

        rendered_content_fragments = []
        for plugin_instance in plugins:
            logger.debug("rendering plugin: %s", plugin_instance)
            rendered_content = renderer.render_plugin(
                instance=plugin_instance,
                context=Context({"request": request}),
                placeholder=placeholder,
            )
            rendered_content_fragments.append(rendered_content)
            logger.debug(
                "rendered content: %s",
                rendered_content
                if len(rendered_content) < 128
                else rendered_content[:128] + "...",
            )

        return "\n".join(rendered_content_fragments)

    return ""


def render_full_page(page: Page, *, as_user: User | None = None):
    """
    Render a full Django CMS page with container template in Django CMS 3.11
    """
    request = get_request(user=as_user, page=page)

    # Use the render_page function
    rendered_response = render_page(request, page, current_language="nl", slug=None)
    rendered_response.render()
    return rendered_response.content


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
    p = api.create_page(
        (title or hook_class.name),
        "cms/fullwidth.html",
        "nl",
        slug=hook_class.app_name,
        apphook=hook_class.__name__,
        apphook_namespace=hook_class.app_name,
        in_navigation=True,
        parent=parent_page,
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

    if publish and not p.publish("nl"):
        raise Exception("failed to publish page")

    return p


def create_cms_page_with_content(
    *, title: str, content: str, language: str = "nl"
) -> Page:
    """Create a CMS page with `content` text in the content slot."""
    page = api.create_page(title, "cms/fullwidth.html", language, in_navigation=True)
    if not page.publish(language):
        raise Exception("failed to publish page")

    content_placeholder = page.placeholders.get(slot="content")
    add_plugin(
        placeholder=content_placeholder,
        plugin_type="TextPlugin",
        language="nl",
        body=content,
    )

    return page
