import logging
from typing import List, TypedDict

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, resolve, reverse
from django.utils.translation import get_language, gettext_lazy as _

from cms.models import Page
from menus.base import NavigationNode
from menus.menu_pool import menu_pool

from open_inwoner.cms.extensions.models import CommonExtension

register = template.Library()
logger = logging.getLogger(__name__)


class MenuItem(TypedDict):
    href: str
    label: str
    icon: str | None
    current: bool
    counter: int | None


class SideNavMenuData:
    """Generate data for the React side navigation meny."""

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
                            "Found icon via CommonExtension%s: %s",
                            page_type,
                            common_ext.menu_icon,
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
                    extra={"indicator": indicator},
                )

        return None

    def _is_current_page(self, node: NavigationNode) -> bool:
        current = node.is_selected(self.request)

        # Fallback to URL path matching if CMS selection isn't working. This is mostly
        # needed to have some test coverage, because the test setup to get
        # node.is_selected worked is too convoluted.
        if not current:
            current = self.request.path == node.get_absolute_url()

        # Handle special case where route doesn't match CMS page URLs
        try:
            resolved = resolve(self.request.path)
            if resolved.url_name == "contactmoment_list":
                current = "contactmomenten" in node.get_absolute_url()
        except Exception as e:
            logger.debug("Could not resolve current path for menu highlighting: %s", e)

        return current

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
                            extra={"page": page},
                        )

                logger.debug(
                    "Skipping node %s for staff user: not published and no content for language %s",
                    node.title,
                    current_language,
                )
                return False

            # Regular users only see published (non-draft) pages
            if is_draft:
                logger.debug(
                    "Skipping node %s for regular user: page is draft", node.title
                )
                return False

            if not is_published_for_language:
                logger.debug(
                    "Skipping node %s for regular user: not published for language %s",
                    node.title,
                    current_language,
                )
                return False

            return True

        except (Page.DoesNotExist, AttributeError):
            logger.warning(
                "Unable to determine publication status for node %s (id=%s): page not found or missing attributes",
                getattr(node, "title", "Unknown"),
                getattr(node, "id", "Unknown"),
            )
            return False

    def _should_include_node(self, node: NavigationNode) -> bool:
        url = node.get_absolute_url()

        for excluded_url in self.exclude_urls_from_menu:
            try:
                excluded_url_path = reverse(excluded_url)
                if excluded_url_path in url:
                    logger.debug("Excluding node %s with URL %s", node, url)
                    return False
            except Exception:
                logger.debug("Failed to reverse URL %s", excluded_url, exc_info=True)
                continue

        if not self._is_visible_to_user(node):
            logger.debug("Skipped node: not published %s", node)
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
            logger.debug("Added menu item: %s", menu_item)

        extra_items = self.get_extra_menu_items()
        complete_menu = menu_items + extra_items

        logger.debug(
            "Base menu items: %s, Extra items: %s, Total: %s",
            len(menu_items),
            len(extra_items),
            len(complete_menu),
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
            logger.warning("Could not add FAQ menu item: %s", exc_info=True)
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

        logger.debug("Generated %s extra menu items", len(extra_items))
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
