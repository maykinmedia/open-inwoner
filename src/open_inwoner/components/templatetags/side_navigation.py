import contextlib

from django import template

from menus.menu_pool import menu_pool

register = template.Library()


@register.simple_tag(takes_context=True)
def react_sidenav_data(context):
    """Template tag to provide menu data for React Sidenav component"""
    request = context["request"]

    try:
        # Get the menu renderer
        renderer = menu_pool.get_renderer(request)

        # Get all menu nodes
        all_nodes = renderer.get_nodes()
        print(f"Total nodes found: {len(all_nodes)}")

        # Find the "home" node - users are required to set this ID!
        # else we need to exclude all the other pages from this menu node
        home_node = None
        for node in all_nodes:
            # Check if this is the home page
            if (
                (hasattr(node, "id") and node.id == "home")
                or (hasattr(node, "reverse_id") and node.reverse_id == "home")
                or (
                    getattr(node, "title", "").lower() == "overzicht"
                    and node.get_absolute_url() == "/"
                )
            ):
                home_node = node
                print(f"Found home node: {node.title}")
                break

        if not home_node:
            print(
                "ERROR: Home node not found! Users must set reverse_id='home' on homepage."
            )
            return []

        # Use children of home node
        target_nodes = getattr(home_node, "children", [])
        print(f"Home node has {len(target_nodes)} children")

        menu_items = []

        # Process the home node children
        for node in target_nodes:
            print(f"Processing node: {getattr(node, 'title', 'NO_TITLE')}")

            # Skip hidden items
            if not getattr(node, "visible", True):
                print("  Skipping invisible node")
                continue

            # Skip items without proper attributes
            if not hasattr(node, "get_menu_title"):
                print("  Skipping node without get_menu_title")
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
                print("  Skipping node without URL")
                continue

            # Extract icon
            icon = ""  # Default: empty (no icon) for municipalities that don't configure icons

            # Try multiple ways to get the icon
            if hasattr(node, "common") and hasattr(node.common, "menu_icon"):
                icon = node.common.menu_icon
                print(f"  Found icon via node.common.menu_icon: {icon}")
            elif hasattr(node, "menu_icon"):
                icon = node.menu_icon
                print(f"  Found icon via node.menu_icon: {icon}")
            elif hasattr(node, "attr") and hasattr(node.attr, "menu_icon"):
                icon = node.attr.menu_icon
                print(f"  Found icon via node.attr.menu_icon: {icon}")
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
                            print(f"  Found icon via CommonExtension: {icon}")
                except Exception as icon_error:
                    print(f"  Could not get icon from CommonExtension: {icon_error}")

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
            print(
                f"  Added menu item: {menu_item['label']} -> {menu_item['href']} (icon: {menu_item['icon']})"
            )

        print(f"Final menu_items: {menu_items}")
        return menu_items

    except Exception as e:
        print(f"Error loading sidenav menu: {e}")
        import traceback

        traceback.print_exc()
        return []
