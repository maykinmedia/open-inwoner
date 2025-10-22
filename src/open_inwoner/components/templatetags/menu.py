from typing import List, TypedDict, cast
from urllib.parse import urlparse

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from django.urls import NoReverseMatch, Resolver404, ResolverMatch, resolve, reverse
from django.utils.translation import get_language, gettext_lazy as _

import structlog
from cms.models import Page
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

from open_inwoner.cms.extensions.models import CommonExtension

register = template.Library()

logger = structlog.stdlib.get_logger(__name__)


class MenuItem(TypedDict):
    href: str
    label: str
    icon: str | None
    current: bool
    counter: int | None


class SideNavMenuData:
    """Generate data for the React side navigation meny."""

    request: HttpRequest

    exclude_urls_from_menu = [
        "profile:detail",
    ]
    """List of URL names that will be excluded from the sidenav menu."""

    def __init__(self, context, root_id: str = "home"):
        self.context = context
        self.root_id = root_id
        try:
            self.request = context["request"]
        except KeyError as exc:
            raise ValueError("Your context must include a request") from exc

    def get_menu_data(self) -> List[MenuItem]:
        # NOTE: This logic is adopted from the ShowMenuBelowId class in menus. We follow
        # the basic processing steps included there.
        menu_renderer = self.context.get("cms_menu_renderer")
        if not menu_renderer:
            menu_renderer = menu_pool.get_renderer(self.request)

        # Get nodes using the root_id
        nodes = menu_renderer.get_nodes(namespace=None, root_id=self.root_id)
        target_nodes: List[NavigationNode] = []

        if not (
            id_nodes := menu_pool.get_nodes_by_attribute(
                nodes,
                "reverse_id",
                self.root_id,
            )
        ):
            raise ImproperlyConfigured(
                "You must define a root CMS page with reverse_id='home' to show the "
                "side navigation menu"
            )

        # Flatten list to avoid recursion
        node = id_nodes[0]
        target_nodes = node.children
        for remove_parent in target_nodes:
            remove_parent.parent = None

        # Apply modifiers
        target_nodes = menu_renderer.apply_modifiers(
            target_nodes, namespace=None, root_id=self.root_id, post_cut=True
        )

        return self._process_nodes_to_json(target_nodes)

    def _extract_icon(self, node: NavigationNode) -> str | None:
        if not (node_id := getattr(node, "id", None)):
            return None

        try:
            page = Page.objects.get(pk=node_id)

            def try_get_icon(page_obj, page_type=""):
                """Helper to try getting icon from a page's CommonExtension"""
                try:
                    common_ext = CommonExtension.objects.get(extended_object=page_obj)
                    if common_ext.menu_icon:
                        logger.debug(
                            "Found icon via CommonExtension",
                            page_type=page_type,
                            icaon=common_ext.menu_icon,
                        )
                        return common_ext.menu_icon
                except CommonExtension.DoesNotExist:
                    pass
                return None

            # Try current page first
            if icon := try_get_icon(page):
                return icon

            # If not found and this is a public page, try the draft version
            if not page.publisher_is_draft and hasattr(page, "publisher_public"):
                try:
                    draft_page = page.publisher_public
                    if icon := try_get_icon(draft_page, " on draft"):
                        return icon
                except AttributeError:
                    pass

            # If not found and this is a draft page, try the public version
            if page.publisher_is_draft and getattr(page, "publisher_public_id", None):
                try:
                    public_page = Page.objects.get(
                        pk=getattr(page, "publisher_public_id")
                    )
                    if icon := try_get_icon(public_page, " on public"):
                        return icon
                except Page.DoesNotExist:
                    pass

        except Exception:
            logger.exception("Error extracting icon")

        return None

    def _extract_counter(self, node: NavigationNode) -> int | None:
        # Check if the node already has a counter indicator
        indicator = getattr(node, "indicator", None)
        if indicator and str(indicator) != "0":
            try:
                return int(indicator)
            except (ValueError, TypeError):
                logger.warning(
                    "Got a menu indicator value that cannot be coerced to int",
                    indicator=indicator,
                )

        return None

    def _is_current_page(self, node: NavigationNode) -> bool:
        if not (resolved_current_path := self.request.resolver_match):
            logger.debug(
                "No resolver match found for current request: node cannot be active",
                node=node,
            )
            return False

        # Build qualified URL name for current path (namespace:url_name)
        current_qualified_name = self._get_qualified_url_name(resolved_current_path)
        logger.debug(
            "Current page qualified URL name",
            qualified_name=current_qualified_name,
        )

        # Handle special case of redirect routes, where the route of the node is
        # actually a redirect to another page: we want to verify if we're on the
        # redirect target, not the node path.
        try:
            if redirect_url := node.attr.get("redirect_url", None):
                logger.debug(
                    "Node has redirect_url configured",
                    node=node,
                    redirect_url=redirect_url,
                )
                try:
                    resolved_redirect_url = resolve(redirect_url)
                    redirect_qualified_name = self._get_qualified_url_name(
                        resolved_redirect_url
                    )
                    logger.debug(
                        "Redirect target qualified URL name",
                        redirect_qualified_name=redirect_qualified_name,
                    )
                    if current_qualified_name == redirect_qualified_name:
                        logger.debug(
                            "Node redirect target matches current page: marking as active",
                            node=node,
                            redirect_target=redirect_qualified_name,
                            current_page=current_qualified_name,
                        )
                        return True
                    else:
                        logger.debug(
                            "Node redirect target does not match current page",
                            node=node,
                            redirect_target=redirect_qualified_name,
                            current_page=current_qualified_name,
                        )
                except Resolver404:
                    logger.debug(
                        "Could not resolve redirect_url for node",
                        redirect_url=redirect_url,
                        node=node,
                    )

            node_absolute_url = node.get_absolute_url()
            resolved_node_path = resolve(node_absolute_url)
            node_qualified_name = self._get_qualified_url_name(resolved_node_path)
            logger.debug(
                "Node qualified URL name",
                node=node,
                qualified_name=node_qualified_name,
            )

            # For CMS pages (and other catch-all patterns), URL names match but paths differ.
            # When URL names match, also verify the actual paths match.
            if is_match := current_qualified_name == node_qualified_name:
                is_match = self.request.path == node_absolute_url
                logger.debug(
                    "URL names match - comparing paths",
                    request_path=self.request.path,
                    node_url=node_absolute_url,
                    result="match" if is_match else "no match",
                )

            logger.debug(
                "Node URL name comparison with current page",
                node=node,
                node_url_name=node_qualified_name,
                result="matches" if is_match else "does not match",
                current_page=current_qualified_name,
            )
            return is_match

        except Exception as e:
            logger.debug(
                "Failed to resolve node for menu highlighting",
                node=node,
                error=e,
            )

        logger.debug("Node is not active (fallthrough)", node=node)
        return False

    def _get_qualified_url_name(self, resolved_match: ResolverMatch) -> str:
        """Build qualified URL name including namespace (e.g., 'namespace:url_name')"""
        if resolved_match.namespaces:
            namespace = ":".join(resolved_match.namespaces)
            return f"{namespace}:{resolved_match.url_name}"

        return cast(str, resolved_match.url_name)

    def _is_visible_to_user(self, node: NavigationNode) -> bool:
        try:
            # Note how draft status works: there are typically two physical Page objects
            # for the same logical page: one draft, one published. Which one is returned
            # depends on the request context, and is handled by Django CMS, by selecting
            # the appropriate node for that context. Thus, we can assume `node` will
            # contain the relevant ID for the current context.
            page = Page.objects.get(pk=node.id)
            current_language = get_language()
            is_published_for_language = page.is_published(current_language)
            is_draft = page.publisher_is_draft
            is_staff = self.request.user.is_staff

            # Staff users can see all pages (including drafts) if published for language
            # OR if it's a draft page with content in the current language
            if is_staff:
                if is_published_for_language:
                    return True

                # For unpublished draft pages, check if they have content in current
                # language as a hack to answer the question "Does the unpublished draft
                # version have any content?". This allows staff users to still see the
                # menu when they are in edit mode.
                if is_draft:
                    try:
                        title = page.get_title_obj(
                            language=current_language, fallback=False
                        )
                        if title:
                            return True
                    except Exception:
                        logger.warning(
                            "unable to get page title for the current node",
                            page=page,
                        )

                logger.debug(
                    "Skipping node for staff user: not published and no content for language",
                    node_title=node.title,
                    language=current_language,
                )
                return False

            # Regular users only see published (non-draft) pages
            if is_draft:
                logger.debug(
                    "Skipping node for regular user: page is draft",
                    node_title=node.title,
                )
                return False

            if not is_published_for_language:
                logger.debug(
                    "Skipping node for regular user: not published for language",
                    node_title=node.title,
                    language=current_language,
                )
                return False

            return True

        except (Page.DoesNotExist, AttributeError):
            logger.warning(
                "Unable to determine publication status for node: page not found or missing attributes",
                node_title=getattr(node, "title", "Unknown"),
                node_id=getattr(node, "id", "Unknown"),
            )
            return False

    def _should_include_node(self, node: NavigationNode) -> bool:
        url = node.get_absolute_url()

        for excluded_url in self.exclude_urls_from_menu:
            try:
                excluded_url_path = reverse(excluded_url)
                if excluded_url_path in url:
                    logger.debug("Excluding node with URL", node=node, url=url)
                    return False
            except Exception:
                logger.debug(
                    "Failed to reverse URL",
                    excluded_url=excluded_url,
                    exc_info=True,
                )
                continue

        if not self._is_visible_to_user(node):
            logger.debug("Skipped node: not published", node=node)
            return False

        return True

    def _process_nodes_to_json(
        self, target_nodes: List[NavigationNode]
    ) -> List[MenuItem]:
        menu_items: List[MenuItem] = []

        for node in filter(self._should_include_node, target_nodes):
            url = node.get_absolute_url()
            icon = self._extract_icon(node)
            counter = self._extract_counter(node)
            current = self._is_current_page(node)

            menu_item: MenuItem = {
                "href": url,
                "label": node.get_menu_title(),
                "icon": icon,
                "current": current,
                "counter": counter,
            }

            menu_items.append(menu_item)
            logger.debug("Added menu item", menu_item=menu_item)

        extra_items = self.get_extra_menu_items()
        complete_menu = menu_items + extra_items

        logger.debug(
            "Menu items counts",
            base_items=len(menu_items),
            extra_items=len(extra_items),
            total=len(complete_menu),
        )
        return complete_menu

    def get_extra_menu_items(self) -> List[MenuItem]:
        extra_items: List[MenuItem] = []
        request = self.context.get("request")
        if not request and hasattr(request, "path"):
            return extra_items

        if not self.context.get("has_general_faq_questions", False):
            return extra_items

        # FAQ item
        is_current = False

        try:
            faq_url = reverse("general_faq")
            is_current = request.path.startswith(faq_url)
        except NoReverseMatch:
            logger.warning("Could not add FAQ menu item", exc_info=True)
            return extra_items

        extra_items.append(
            {
                "href": faq_url,
                "label": str(_("Veelgestelde vragen")),
                "icon": "question_answer",
                "current": is_current,
                "counter": None,
            }
        )

        logger.debug("Generated extra menu items", count=len(extra_items))
        return extra_items


@register.simple_tag(takes_context=True)
def react_sidenav_data(context):
    """Template tag to provide menu data for React SideNavModule component"""

    try:
        side_nav_menu = SideNavMenuData(context, root_id="home")
        return side_nav_menu.get_menu_data()
    except Exception:
        logger.exception("Error loading sidenav menu")
        return []


@register.simple_tag(takes_context=True)
def has_sidenav_items(context):
    """
    Check if there are any menu items.
    If False then sidebar should be hidden and main content should be fullwidth
    """
    if not context["request"].user.is_authenticated:
        return False

    menu_data = react_sidenav_data(context)
    return len(menu_data) > 0


@register.simple_tag(takes_context=True)
def show_full_dropdown_menu(context) -> bool:
    """
    Determines whether the full dropdown menu should be shown.

    This is to avoid showing the full menu in the dropdown when those same items are
    already displayed in the side menu.
    """
    request = context["request"]

    if not request.resolver_match:
        return True  # Show all items when URL resolution fails

    current_url_name = request.resolver_match.url_name
    current_namespace = (
        request.resolver_match.namespaces[0]
        if request.resolver_match.namespaces
        else None
    )
    current_qualified_url_name = (
        f"{current_namespace}:{current_url_name}"
        if current_namespace
        else current_url_name
    )

    # The following URLs are expected to have the sidenav, so they only need a minimal
    # dropdown menu.
    urls_with_minimal_dropdown_menu = {
        "pages-root",
        "general_faq",
        "collaborate:plan_list",
        "ssd:uitkeringen",
        "products:category_list",
        "cases:index",
        "cases:contactmoment_list",
        "profile:appointments",
    }

    is_url_with_minimal_dropdown = (
        current_qualified_url_name in urls_with_minimal_dropdown_menu
    )
    should_show_full_dropdown_menu = not is_url_with_minimal_dropdown

    if not should_show_full_dropdown_menu:
        logger.debug(
            "Menu items hidden from dropdown menu",
            extra={
                "current_url_name": current_url_name,
                "current_namespace": current_namespace,
                "current_qualified_url_name": current_qualified_url_name,
                "excluded": is_url_with_minimal_dropdown,
                "show_menu": should_show_full_dropdown_menu,
            },
        )

    return should_show_full_dropdown_menu


@register.simple_tag(takes_context=True)
def should_show_menu_item_in_dropdown(context, menu_item_url: str) -> bool:
    """
    Determines whether a specific menu item should be shown in the dropdown.

    When the side navigation is active, only show "My Profile" (profile:detail) in the
    dropdown. Otherwise, show all items.

    Args:
        context: Template context
        menu_item_url: The URL of the menu item to check

    Returns:
        True if the item should be shown, False otherwise
    """
    # If the full dropdown menu should be shown, all items are visible
    if show_full_dropdown_menu(context):
        return True

    if not menu_item_url:
        logger.warning(
            "Empty menu item url passed to dropdown menu",
            extra={"menu_item_url": menu_item_url},
        )
        return False

    # When side nav is active, only show these items
    allowed_url_names_in_minimal_dropdown = {
        "profile:detail",
    }

    try:
        # Handle the edge case where the URL is a qualified URL (e.g. through a redirect
        # url field). If we've just received a path, this won't change the behaviour.
        parsed = urlparse(menu_item_url)
        resolved_menu_item = resolve(parsed.path)

        # Build qualified URL name from resolved match
        if resolved_menu_item.namespaces:
            namespace = ":".join(resolved_menu_item.namespaces)
            menu_item_qualified_name = f"{namespace}:{resolved_menu_item.url_name}"
        else:
            menu_item_qualified_name = cast(str, resolved_menu_item.url_name)

        return menu_item_qualified_name in allowed_url_names_in_minimal_dropdown
    except Resolver404:
        logger.warning(
            "Could not resolve menu item URL: %s", menu_item_url, exc_info=True
        )
        # If we can't determine the URL, do not show it (we're working on an allowlist
        # principle)
        return False
