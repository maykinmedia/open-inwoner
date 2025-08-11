import contextlib
import logging

from django import template

from menus.menu_pool import menu_pool

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=True)
def react_sidenav_data(context):
    """Template tag to provide menu data for React SideNavModule component"""
    request = context["request"]

    try:
        # Get the menu renderer
        renderer = menu_pool.get_renderer(request)

        # Get all menu nodes
        all_nodes = renderer.get_nodes()
        logger.debug("Total nodes found: %s", len(all_nodes))

        # Find the "home" node first (preferred method)
        home_node = None
        for node in all_nodes:
            # Check if this is the home page via node.attr.reverse_id
            node_attr = getattr(node, "attr", {})
            if node_attr.get("reverse_id", None) == "home":
                home_node = node
                logger.debug("Found home node: %s", node.title)
                break

        # Determine which nodes to use
        if home_node:
            # Use children of home node (preferred)
            target_nodes = getattr(home_node, "children", [])
            logger.debug("Using home node children: %s items", len(target_nodes))
        else:
            # Fallback: use all visible nodes
            logger.warning(
                "Home node not found (reverse_id='home' not set). Using all visible pages as fallback."
            )

            target_nodes = []
            for node in all_nodes:
                # Only include visible nodes
                if getattr(node, "visible", True):
                    target_nodes.append(node)

            logger.debug(
                "Using fallback nodes (all visible): %s items", len(target_nodes)
            )

        menu_items = []

        # Process the target nodes
        for node in target_nodes:
            logger.debug("Processing node: %s", getattr(node, "title", "NO_TITLE"))

            # Skip hidden items
            if not getattr(node, "visible", True):
                logger.debug("  Skipping invisible node")
                continue

            # Skip items without proper attributes
            if not hasattr(node, "get_menu_title"):
                logger.debug("Skipping node without get_menu_title")
                continue

            # Extract URL
            url = None
            if (
                hasattr(node, "attr")
                and hasattr(node.attr, "redirect_url")
                and node.attr.redirect_url
            ):
                url = node.attr.redirect_url
            elif hasattr(node, "get_absolute_url"):
                url = node.get_absolute_url()
            else:
                logger.debug("Skipping node without URL")
                continue

            # Extract icon
            icon = ""  # Default: empty (no icon) for municipalities that don't configure icons

            # Try multiple ways to get the icon
            if hasattr(node, "common") and hasattr(node.common, "menu_icon"):
                icon = node.common.menu_icon
                logger.debug("Found icon via node.common.menu_icon: %s", icon)
            elif hasattr(node, "menu_icon"):
                icon = node.menu_icon
                logger.debug("Found icon via node.menu_icon: %s", icon)
            elif hasattr(node, "attr") and hasattr(node.attr, "menu_icon"):
                icon = node.attr.menu_icon
                logger.debug("Found icon via node.attr.menu_icon: %s", icon)
            else:
                # Try to get it from the page's CommonExtension
                try:
                    if hasattr(node, "id") and node.id:
                        from cms.models import Page

                        from open_inwoner.cms.extensions.models import CommonExtension

                        page = Page.objects.get(pk=node.id)
                        common_ext = CommonExtension.objects.get(extended_object=page)
                        if common_ext.menu_icon:
                            icon = common_ext.menu_icon
                            logger.debug("  Found icon via CommonExtension: %s", icon)
                except Exception as icon_error:
                    logger.debug(
                        "Could not get icon from CommonExtension: %s", icon_error
                    )

            # Extract indicator/counter
            counter = None
            if (
                hasattr(node, "indicator")
                and node.indicator
                and str(node.indicator) != "0"
            ):
                with contextlib.suppress(ValueError, TypeError):
                    counter = int(node.indicator)

            # Check if current page
            current = getattr(node, "selected", False)

            menu_item = {
                "href": url,
                "label": node.get_menu_title(),
                "icon": icon,
                "current": current,
                "counter": counter,
            }

            menu_items.append(menu_item)
            logger.debug(
                "Added menu item: %s -> %s (icon: %s)",
                menu_item["label"],
                menu_item["href"],
                menu_item["icon"],
            )

        logger.debug("Final menu_items count: %s", len(menu_items))
        return menu_items

    except Exception as e:
        logger.exception("Error loading sidenav menu: %s", e)
        return []
