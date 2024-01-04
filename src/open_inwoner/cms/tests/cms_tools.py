from typing import Tuple

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.utils.module_loading import import_string

from cms import api
from cms.api import add_plugin
from cms.app_base import CMSApp
from cms.models import Placeholder
from cms.plugin_rendering import ContentRenderer

from open_inwoner.cms.extensions.models import CommonExtension


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


def _init_plugin(plugin_class, plugin_data=None) -> Tuple[dict, str]:
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


def get_request(*, user=None, session_vars=None):
    request = RequestFactory().get("/")
    if user:
        request.user = user
    else:
        request.user = AnonymousUser()
    middleware = SessionMiddleware()
    middleware.process_request(request)
    if session_vars:
        request.session.update(session_vars)
    request.session.save()
    return request


def render_plugin(
    plugin_class, plugin_data=None, *, user=None, session_vars=None
) -> Tuple[str, dict]:
    model_instance = _init_plugin(plugin_class, plugin_data)
    request = get_request(user=user, session_vars=session_vars)

    context = apply_context_processors(request)

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

    # TODO find out why this doesn't work
    # create app_config
    # if hook_class.app_config:
    #     # attach it to the page for convenience
    #     if config_args is None:
    #         config_args = dict()
    #     config_args["namespace"] = hook_class.app_name
    #     p.app_config = hook_class.app_config.objects.create(**config_args)

    if not p.publish("nl"):
        raise Exception("failed to publish page")

    return p
