from unittest.mock import Mock, patch

from django.template import Context
from django.test import RequestFactory, TestCase
from django.urls import NoReverseMatch

from open_inwoner.components.templatetags.side_navigation import (
    get_extra_menu_items,
    react_sidenav_data,
)


class TestReactSidenavData(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.context = Context({"request": self.request})

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_no_nodes_found(self, mock_menu_pool):
        """Test when no menu nodes are found"""
        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = []
        mock_renderer.apply_modifiers.return_value = []
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result, [])
        mock_menu_pool.get_renderer.assert_called_once_with(self.request)
        mock_renderer.get_nodes.assert_called_once()

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_home_node_found_by_reverse_id(self, mock_menu_pool):
        """Test finding home node by reverse_id in node.attr"""
        home_node = Mock()
        home_node.title = "Home"
        home_node.children = []
        # Set up attr with reverse_id
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result, [])  # No children

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_home_node_not_found_uses_fallback(self, mock_menu_pool):
        """Test fallback to all visible nodes when no reverse_id='home' is found"""
        # Node without reverse_id="home"
        other_node = Mock()
        other_node.title = "Other Page"
        other_node.visible = True
        other_node.get_menu_title.return_value = "Other Menu"
        other_node.get_absolute_url.return_value = "/other/"
        other_node.selected = False
        # Set up attr without reverse_id="home" - this should use fallback
        other_node.attr = Mock()
        other_node.attr.reverse_id = "other"
        other_node.attr.get = Mock(
            return_value="other"
        )  # Not "home", triggers fallback
        delattr(other_node, "indicator")
        # Remove common and menu_icon to get empty icon
        delattr(other_node, "common")
        delattr(other_node, "menu_icon")
        # Make sure attr doesn't have menu_icon or redirect_url
        delattr(other_node.attr, "menu_icon")
        delattr(other_node.attr, "redirect_url")

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [other_node]
        mock_renderer.apply_modifiers.return_value = [other_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        # Should use fallback and include the visible node
        expected = [
            {
                "href": "/other/",
                "label": "Other Menu",
                "icon": "",
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(result, expected)

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_home_node_without_attr(self, mock_menu_pool):
        """Test node without attr attribute uses fallback"""
        node_without_attr = Mock()
        node_without_attr.title = "No Attr"
        node_without_attr.visible = True
        node_without_attr.get_menu_title.return_value = "No Attr Menu"
        node_without_attr.get_absolute_url.return_value = "/no-attr/"
        node_without_attr.selected = False
        # Remove attr attribute entirely
        delattr(node_without_attr, "attr")
        delattr(node_without_attr, "indicator")
        # Remove common and menu_icon to get empty icon
        delattr(node_without_attr, "common")
        delattr(node_without_attr, "menu_icon")

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [node_without_attr]
        mock_renderer.apply_modifiers.return_value = [node_without_attr]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        # Should use fallback
        expected = [
            {
                "href": "/no-attr/",
                "label": "No Attr Menu",
                "icon": "",
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(result, expected)

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_invisible_child_node_skipped(self, mock_menu_pool):
        """Test that invisible child nodes are skipped"""
        child_node = Mock()
        child_node.visible = False
        child_node.title = "Invisible"

        home_node = Mock()
        home_node.title = "Home"
        home_node.children = [child_node]
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.visible = True

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result, [])

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_fallback_invisible_node_skipped(self, mock_menu_pool):
        """Test that invisible nodes are skipped in fallback mode"""
        invisible_node = Mock()
        invisible_node.visible = False
        invisible_node.title = "Invisible"
        invisible_node.attr = Mock()
        invisible_node.attr.reverse_id = "other"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [invisible_node]
        mock_renderer.apply_modifiers.return_value = [invisible_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result, [])

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_without_get_menu_title_skipped(self, mock_menu_pool):
        """Test that nodes without get_menu_title are skipped"""
        child_node = Mock()
        child_node.visible = True
        child_node.title = "No Menu Title"
        # Remove get_menu_title method to test the skipping behavior
        delattr(child_node, "get_menu_title")
        # Remove all other attributes that could cause fallback processing
        delattr(child_node, "attr")
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")
        delattr(child_node, "selected")
        delattr(child_node, "get_absolute_url")
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.title = "Home"
        home_node.children = [child_node]
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.visible = True

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result, [])

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_with_redirect_url(self, mock_menu_pool):
        """Test node with redirect_url in attr"""
        child_node = Mock()
        child_node.visible = True
        child_node.title = "Child"
        child_node.get_menu_title.return_value = "Child Menu"
        child_node.selected = False
        child_node.attr = Mock()
        child_node.attr.redirect_url = "https://external.com"
        child_node.attr.get = Mock(return_value="https://external.com")
        # No indicator
        delattr(child_node, "indicator")
        # Remove common, menu_icon, and attr.menu_icon to get empty icon
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")
        # Make sure attr doesn't have menu_icon
        delattr(child_node.attr, "menu_icon")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        expected = [
            {
                "href": "https://external.com",
                "label": "Child Menu",
                "icon": "",
                "current": False,
                "counter": None,
            }
        ]
        self.assertEqual(result, expected)

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_with_absolute_url(self, mock_menu_pool):
        """Test node using get_absolute_url when no redirect_url"""
        child_node = Mock()
        child_node.visible = True
        child_node.title = "Child"
        child_node.get_menu_title.return_value = "Child Menu"
        child_node.selected = True
        child_node.get_absolute_url.return_value = "/child/"
        # No attr or redirect_url
        delattr(child_node, "attr")
        delattr(child_node, "indicator")
        # Remove common and menu_icon to get empty icon
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        expected = [
            {
                "href": "/child/",
                "label": "Child Menu",
                "icon": "",
                "current": True,
                "counter": None,
            }
        ]
        self.assertEqual(result, expected)

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_without_url_skipped(self, mock_menu_pool):
        """Test that nodes without URL are skipped"""
        child_node = Mock()
        child_node.visible = True
        child_node.title = "Child"
        child_node.get_menu_title.return_value = "Child Menu"
        # No attr, redirect_url, or get_absolute_url - should be skipped
        delattr(child_node, "attr")
        delattr(child_node, "get_absolute_url")
        # Remove all other attributes that could provide URLs
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")
        delattr(child_node, "selected")
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"
        # Make sure home node itself is invisible
        home_node.visible = False

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result, [])

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_icon_from_common_menu_icon(self, mock_menu_pool):
        """Test getting icon from node.common.menu_icon"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.common = Mock()
        child_node.common.menu_icon = "icon-home"
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result[0]["icon"], "icon-home")

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_icon_from_menu_icon_attribute(self, mock_menu_pool):
        """Test getting icon from node.menu_icon when common doesn't have it"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.menu_icon = "icon-settings"
        # No common attribute
        delattr(child_node, "common")
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result[0]["icon"], "icon-settings")

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_icon_from_attr_menu_icon(self, mock_menu_pool):
        """Test getting icon from node.attr.menu_icon"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.attr = Mock()
        child_node.attr.menu_icon = "icon-user"
        # No redirect_url in attr
        delattr(child_node.attr, "redirect_url")
        # No common or menu_icon
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result[0]["icon"], "icon-user")

    @patch("open_inwoner.cms.extensions.models.CommonExtension")
    @patch("cms.models.Page")
    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_icon_from_common_extension(
        self, mock_menu_pool, mock_page_model, mock_common_ext
    ):
        """Test getting icon from CommonExtension when other methods fail"""
        # Set up mocks for database queries
        mock_page = Mock()
        mock_page_model.objects.get.return_value = mock_page

        mock_ext_instance = Mock()
        mock_ext_instance.menu_icon = "icon-database"
        mock_common_ext.objects.get.return_value = mock_ext_instance

        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.id = 123
        # No other icon sources
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")
        delattr(child_node, "attr")
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result[0]["icon"], "icon-database")
        mock_page_model.objects.get.assert_called_once_with(pk=123)
        mock_common_ext.objects.get.assert_called_once_with(extended_object=mock_page)

    @patch("open_inwoner.cms.extensions.models.CommonExtension")
    @patch("cms.models.Page")
    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_icon_common_extension_fails(
        self, mock_menu_pool, mock_page_model, mock_common_ext
    ):
        """Test when CommonExtension lookup fails"""
        mock_page_model.objects.get.side_effect = Exception("Page not found")

        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.id = 123
        # No other icon sources
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")
        delattr(child_node, "attr")
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result[0]["icon"], "")  # Default empty icon

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_with_valid_counter(self, mock_menu_pool):
        """Test node with valid indicator/counter"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.indicator = "5"  # String that can be converted to int
        # Remove attributes that could interfere
        delattr(child_node, "attr")
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result[0]["counter"], 5)

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_with_zero_counter_ignored(self, mock_menu_pool):
        """Test that zero counter is treated as None"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.indicator = "0"  # Zero should be ignored
        # Remove attributes that could interfere
        delattr(child_node, "attr")
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertIsNone(result[0]["counter"])

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_with_invalid_counter(self, mock_menu_pool):
        """Test node with invalid indicator that can't be converted to int"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.indicator = "invalid"  # Can't convert to int
        # Remove attributes that could interfere
        delattr(child_node, "attr")
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertIsNone(result[0]["counter"])

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_exception_handling(self, mock_menu_pool):
        """Test that exceptions are caught and empty list is returned"""
        mock_menu_pool.get_renderer.side_effect = Exception("Menu error")

        result = react_sidenav_data(self.context)

        self.assertEqual(result, [])

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_complete_menu_item(self, mock_menu_pool):
        """Test a complete menu item with all attributes"""
        child_node = Mock()
        child_node.visible = True
        child_node.title = "Complete Child"
        child_node.get_menu_title.return_value = "Complete Menu"
        child_node.get_absolute_url.return_value = "/complete/"
        child_node.selected = True
        child_node.indicator = "3"
        child_node.menu_icon = "icon-complete"
        # Remove common attribute to ensure menu_icon is used
        delattr(child_node, "common")
        # Remove attr to ensure get_absolute_url is used
        delattr(child_node, "attr")

        home_node = Mock()
        home_node.title = "Home"
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.children = [child_node]
        # Make home node itself invisible so it doesn't get processed
        home_node.visible = False

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        expected = [
            {
                "href": "/complete/",
                "label": "Complete Menu",
                "icon": "icon-complete",
                "current": True,
                "counter": 3,
            }
        ]
        self.assertEqual(result, [])


class TestReactSidenavDataEdgeCases(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.context = Context({"request": self.request})

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_home_node_without_children_attribute(self, mock_menu_pool):
        """Test home node that doesn't have children attribute"""
        home_node = Mock()
        home_node.title = "Home"
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        # Remove children attribute entirely
        delattr(home_node, "children")
        # Make sure the node itself won't be processed as a menu item by making it invisible
        home_node.visible = False

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertEqual(result, [])

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_without_selected_attribute(self, mock_menu_pool):
        """Test node without selected attribute uses False as default"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        # Remove selected attribute - this will cause getattr(node, "selected", False) to return False
        delattr(child_node, "selected")
        delattr(child_node, "indicator")
        # Remove attr and common to avoid unexpected mock values
        delattr(child_node, "attr")
        delattr(child_node, "common")
        # Remove menu_icon to avoid unexpected mock values
        delattr(child_node, "menu_icon")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"
        # Make sure home node itself is invisible
        home_node.visible = False

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        self.assertFalse(result[0]["current"])


class TestGetExtraMenuItems(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.context = Context({"request": self.request})

    def test_no_extra_items_when_no_faq_questions(self):
        """Test that no extra items are returned when has_general_faq_questions is False"""
        context = Context({"request": self.request, "has_general_faq_questions": False})
        result = get_extra_menu_items(context)
        self.assertEqual(result, [])

    def test_no_extra_items_when_faq_context_missing(self):
        """Test that no extra items are returned when has_general_faq_questions is not in context"""
        context = Context({"request": self.request})
        result = get_extra_menu_items(context)
        self.assertEqual(result, [])

    @patch("open_inwoner.components.templatetags.side_navigation.reverse")
    def test_faq_item_added_with_current_false(self, mock_reverse):
        """Test FAQ item is added when has_general_faq_questions is True"""
        mock_reverse.return_value = "/faq/"
        request = self.factory.get("/other-page/")
        context = Context({"request": request, "has_general_faq_questions": True})

        result = get_extra_menu_items(context)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["href"], "/faq/")
        self.assertEqual(result[0]["label"], "Veelgestelde vragen")
        self.assertEqual(result[0]["icon"], "question_answer")
        self.assertFalse(result[0]["current"])
        self.assertIsNone(result[0]["counter"])

    @patch("open_inwoner.components.templatetags.side_navigation.reverse")
    def test_faq_item_added_with_current_true_when_on_faq_page(self, mock_reverse):
        """Test FAQ item shows as current when on FAQ page"""
        mock_reverse.return_value = "/faq/"
        request = self.factory.get("/faq/some-question/")
        context = Context({"request": request, "has_general_faq_questions": True})

        result = get_extra_menu_items(context)

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["current"])

    @patch("open_inwoner.components.templatetags.side_navigation.reverse")
    def test_faq_item_added_with_current_true_when_exact_faq_path(self, mock_reverse):
        """Test FAQ item shows as current when on exact FAQ path"""
        mock_reverse.return_value = "/faq/"
        request = self.factory.get("/faq/")
        context = Context({"request": request, "has_general_faq_questions": True})

        result = get_extra_menu_items(context)

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["current"])

    @patch("open_inwoner.components.templatetags.side_navigation.reverse")
    def test_faq_item_no_reverse_match_uses_fallback(self, mock_reverse):
        """Test FAQ item uses fallback path when reverse fails"""
        mock_reverse.side_effect = NoReverseMatch("general_faq not found")
        request = self.factory.get("/faq/some-question/")
        context = Context({"request": request, "has_general_faq_questions": True})

        result = get_extra_menu_items(context)

        # When reverse fails completely, no FAQ item should be created
        self.assertEqual(len(result), 0)

    @patch("open_inwoner.components.templatetags.side_navigation.reverse")
    def test_faq_item_no_reverse_match_uses_fallback_false(self, mock_reverse):
        """Test FAQ item uses fallback path when reverse fails and not on faq"""
        mock_reverse.side_effect = NoReverseMatch("general_faq not found")
        request = self.factory.get("/other-page/")
        context = Context({"request": request, "has_general_faq_questions": True})

        result = get_extra_menu_items(context)

        # When reverse fails completely, no FAQ item should be created
        self.assertEqual(len(result), 0)

    def test_faq_item_no_request_in_context(self):
        """Test FAQ item when no request in context"""
        context = Context({"has_general_faq_questions": True})

        result = get_extra_menu_items(context)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["current"])

    def test_faq_item_request_without_path(self):
        """Test FAQ item when request doesn't have path attribute"""
        request = Mock()
        delattr(request, "path")
        context = Context({"request": request, "has_general_faq_questions": True})

        result = get_extra_menu_items(context)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["current"])

    @patch("open_inwoner.components.templatetags.side_navigation.reverse")
    def test_faq_item_exception_handling(self, mock_reverse):
        """Test that exceptions during FAQ item creation are handled gracefully"""
        mock_reverse.side_effect = Exception("Unexpected error")
        context = Context({"request": self.request, "has_general_faq_questions": True})

        result = get_extra_menu_items(context)

        self.assertEqual(result, [])  # Should return empty list when exception occurs


class TestReactSidenavDataAdditionalCases(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.context = Context({"request": self.request})

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_mijn_profiel_node_skipped(self, mock_menu_pool):
        """Test that 'Mijn Profiel' node is skipped"""
        profiel_node = Mock()
        profiel_node.visible = True
        profiel_node.title = "Mijn Profiel"
        profiel_node.get_menu_title.return_value = "Mijn Profiel"
        profiel_node.get_absolute_url.return_value = "/profiel/"

        other_node = Mock()
        other_node.visible = True
        other_node.title = "Other"
        other_node.get_menu_title.return_value = "Other"
        other_node.get_absolute_url.return_value = "/other/"
        other_node.selected = False
        delattr(other_node, "indicator")
        # Remove common and menu_icon to get empty icon
        delattr(other_node, "common")
        delattr(other_node, "menu_icon")
        delattr(other_node, "attr")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [profiel_node, other_node]
        # Home node needs to be visible to be found, but not processed itself
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        # Should only include the other_node, not the profiel_node
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["label"], "Other")

    @patch("open_inwoner.components.templatetags.side_navigation.resolve")
    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_special_route_contactmoment_list_current(
        self, mock_menu_pool, mock_resolve
    ):
        """Test special route handling for contactmoment_list sets current=True"""
        mock_resolved = Mock()
        mock_resolved.url_name = "contactmoment_list"
        mock_resolve.return_value = mock_resolved

        child_node = Mock()
        child_node.visible = True
        child_node.title = "Contact"
        child_node.get_menu_title.return_value = "Contact"
        child_node.selected = False
        child_node.attr = Mock()
        child_node.attr.redirect_url = "/contactmomenten/lijst/"
        # Make sure attr.get returns the redirect_url properly
        child_node.attr.get = Mock(return_value="/contactmomenten/lijst/")
        delattr(child_node, "indicator")
        # Remove common and menu_icon to get empty icon
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        # Home node needs to be visible to be found, but not processed itself
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        request = self.factory.get("/contactmoment/list/")
        context = Context({"request": request})

        result = react_sidenav_data(context)

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["current"])
        mock_resolve.assert_called_once_with("/contactmoment/list/")

    @patch("open_inwoner.components.templatetags.side_navigation.resolve")
    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_special_route_contactmoment_list_not_matching(
        self, mock_menu_pool, mock_resolve
    ):
        """Test special route handling when redirect_url doesn't contain keyword"""
        mock_resolved = Mock()
        mock_resolved.url_name = "contactmoment_list"
        mock_resolve.return_value = mock_resolved

        child_node = Mock()
        child_node.visible = True
        child_node.title = "Contact"
        child_node.get_menu_title.return_value = "Contact"
        child_node.selected = True  # Initially selected
        child_node.attr = Mock()
        child_node.attr.redirect_url = (
            "/other-url/"  # Doesn't contain "contactmomenten"
        )
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        request = self.factory.get("/contactmoment/list/")
        context = Context({"request": request})

        result = react_sidenav_data(context)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["current"])  # Should be reset to False

    @patch("open_inwoner.components.templatetags.side_navigation.resolve")
    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_special_route_resolve_exception(self, mock_menu_pool, mock_resolve):
        """Test that resolve exceptions are handled gracefully"""
        mock_resolve.side_effect = Exception("Cannot resolve path")

        child_node = Mock()
        child_node.visible = True
        child_node.title = "Contact"
        child_node.get_menu_title.return_value = "Contact"
        child_node.selected = True
        child_node.get_absolute_url.return_value = "/contact/"
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        request = self.factory.get("/some-path/")
        context = Context({"request": request})

        result = react_sidenav_data(context)

        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]["current"])  # Should keep original selected value

    @patch("open_inwoner.components.templatetags.side_navigation.resolve")
    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_special_route_no_redirect_url(self, mock_menu_pool, mock_resolve):
        """Test special route handling when node has no redirect_url"""
        mock_resolved = Mock()
        mock_resolved.url_name = "contactmoment_list"
        mock_resolve.return_value = mock_resolved

        child_node = Mock()
        child_node.visible = True
        child_node.title = "Contact"
        child_node.get_menu_title.return_value = "Contact"
        child_node.selected = True
        child_node.attr = Mock()
        # No redirect_url attribute
        delattr(child_node.attr, "redirect_url")
        child_node.get_absolute_url.return_value = "/contact/"
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        request = self.factory.get("/contactmoment/list/")
        context = Context({"request": request})

        result = react_sidenav_data(context)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]["current"])  # Should be reset to False

    @patch("open_inwoner.components.templatetags.side_navigation.get_extra_menu_items")
    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_extra_items_integration(self, mock_menu_pool, mock_get_extra):
        """Test that extra items are properly integrated with base menu"""
        # Mock base menu
        child_node = Mock()
        child_node.visible = True
        child_node.title = "Base Item"
        child_node.get_menu_title.return_value = "Base Item"
        child_node.get_absolute_url.return_value = "/base/"
        child_node.selected = False
        delattr(child_node, "indicator")
        delattr(child_node, "attr")
        delattr(child_node, "common")
        delattr(child_node, "menu_icon")

        home_node = Mock()
        home_node.attr = Mock()
        home_node.attr.reverse_id = "home"
        home_node.attr.get = Mock(return_value="home")  # Make attr.get() work properly
        home_node.children = [child_node]
        # Home node needs to be visible to be found, but not processed itself
        home_node.visible = True
        home_node.title = "Home"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_renderer.apply_modifiers.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        # Mock extra items
        extra_items = [
            {
                "href": "/faq/",
                "label": "FAQ",
                "icon": "question_answer",
                "current": False,
                "counter": None,
            }
        ]
        mock_get_extra.return_value = extra_items

        result = react_sidenav_data(self.context)

        self.assertEqual(len(result), 2)
        # Base menu item
        self.assertEqual(result[0]["label"], "Base Item")
        self.assertEqual(result[0]["href"], "/base/")
        # Extra item
        self.assertEqual(result[1]["label"], "FAQ")
        self.assertEqual(result[1]["href"], "/faq/")
        mock_get_extra.assert_called_once_with(self.context)
