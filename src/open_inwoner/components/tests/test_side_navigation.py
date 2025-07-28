from unittest.mock import Mock, patch

from django.template import Context
from django.test import RequestFactory

from open_inwoner.components.templatetags.side_navigation import react_sidenav_data


class TestReactSidenavData:
    def setup_method(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.context = Context({"request": self.request})

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_no_nodes_found(self, mock_menu_pool):
        """Test when no menu nodes are found"""
        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = []
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []
        mock_menu_pool.get_renderer.assert_called_once_with(self.request)
        mock_renderer.get_nodes.assert_called_once()

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_home_node_found_by_id(self, mock_menu_pool):
        """Test finding home node by id attribute"""
        # Create mock nodes
        home_node = Mock()
        home_node.id = "home"
        home_node.title = "Home"
        home_node.children = []

        other_node = Mock()
        other_node.id = "other"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [other_node, home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []  # No children

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_home_node_found_by_reverse_id(self, mock_menu_pool):
        """Test finding home node by reverse_id attribute"""
        home_node = Mock()
        home_node.reverse_id = "home"
        home_node.title = "Home"
        home_node.children = []
        # Make sure it doesn't have id attribute
        del home_node.id

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_home_node_found_by_title_and_url(self, mock_menu_pool):
        """Test finding home node by title 'overzicht' and URL '/'"""
        home_node = Mock()
        home_node.title = "Overzicht"
        home_node.get_absolute_url.return_value = "/"
        home_node.children = []
        # Remove id and reverse_id attributes
        delattr(home_node, "id")
        delattr(home_node, "reverse_id")

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_no_home_node_found(self, mock_menu_pool):
        """Test when no home node is found"""
        other_node = Mock()
        other_node.id = "other"
        other_node.title = "Other"

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [other_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_invisible_child_node_skipped(self, mock_menu_pool):
        """Test that invisible child nodes are skipped"""
        child_node = Mock()
        child_node.visible = False
        child_node.title = "Invisible"

        home_node = Mock()
        home_node.id = "home"
        home_node.title = "Home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_node_without_get_menu_title_skipped(self, mock_menu_pool):
        """Test that nodes without get_menu_title are skipped"""
        child_node = Mock()
        child_node.visible = True
        child_node.title = "No Menu Title"
        # Remove get_menu_title method
        del child_node.get_menu_title

        home_node = Mock()
        home_node.id = "home"
        home_node.title = "Home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_node_with_redirect_url(self, mock_menu_pool):
        """Test node with redirect_url in attr"""
        child_node = Mock()
        child_node.visible = True
        child_node.title = "Child"
        child_node.get_menu_title.return_value = "Child Menu"
        child_node.selected = False
        child_node.attr = Mock()
        child_node.attr.redirect_url = "https://external.com"
        # No indicator
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
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
        assert result == expected

    @patch("your_app.templatetags.your_templatetags.menu_pool")
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

        home_node = Mock()
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
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
        assert result == expected

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_node_without_url_skipped(self, mock_menu_pool):
        """Test that nodes without URL are skipped"""
        child_node = Mock()
        child_node.visible = True
        child_node.title = "Child"
        child_node.get_menu_title.return_value = "Child Menu"
        # No attr, redirect_url, or get_absolute_url
        delattr(child_node, "attr")
        delattr(child_node, "get_absolute_url")

        home_node = Mock()
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []

    @patch("your_app.templatetags.your_templatetags.menu_pool")
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
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["icon"] == "icon-home"

    @patch("your_app.templatetags.your_templatetags.menu_pool")
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
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["icon"] == "icon-settings"

    @patch("your_app.templatetags.your_templatetags.menu_pool")
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
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["icon"] == "icon-user"

    @patch("your_app.templatetags.your_templatetags.CommonExtension")
    @patch("your_app.templatetags.your_templatetags.Page")
    @patch("your_app.templatetags.your_templatetags.menu_pool")
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
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["icon"] == "icon-database"
        mock_page_model.objects.get.assert_called_once_with(pk=123)
        mock_common_ext.objects.get.assert_called_once_with(extended_object=mock_page)

    @patch("your_app.templatetags.your_templatetags.CommonExtension")
    @patch("your_app.templatetags.your_templatetags.Page")
    @patch("your_app.templatetags.your_templatetags.menu_pool")
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
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["icon"] == ""  # Default empty icon

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_node_with_valid_counter(self, mock_menu_pool):
        """Test node with valid indicator/counter"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.indicator = "5"  # String that can be converted to int

        home_node = Mock()
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["counter"] == 5

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_node_with_zero_counter_ignored(self, mock_menu_pool):
        """Test that zero counter is treated as None"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.indicator = "0"  # Zero should be ignored

        home_node = Mock()
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["counter"] is None

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_node_with_invalid_counter(self, mock_menu_pool):
        """Test node with invalid indicator that can't be converted to int"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        child_node.selected = False
        child_node.indicator = "invalid"  # Can't convert to int

        home_node = Mock()
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["counter"] is None

    @patch("your_app.templatetags.your_templatetags.menu_pool")
    def test_exception_handling(self, mock_menu_pool):
        """Test that exceptions are caught and empty list is returned"""
        mock_menu_pool.get_renderer.side_effect = Exception("Menu error")

        result = react_sidenav_data(self.context)

        assert result == []

    @patch("your_app.templatetags.your_templatetags.menu_pool")
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

        home_node = Mock()
        home_node.id = "home"
        home_node.title = "Home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
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
        assert result == expected


# Additional test for edge cases not covered above
class TestReactSidenavDataEdgeCases:
    def setup_method(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.context = Context({"request": self.request})

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_home_node_without_children_attribute(self, mock_menu_pool):
        """Test home node that doesn't have children attribute"""
        home_node = Mock()
        home_node.id = "home"
        home_node.title = "Home"
        # Remove children attribute entirely
        delattr(home_node, "children")

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result == []

    @patch("open_inwoner.components.templatetags.side_navigation.menu_pool")
    def test_node_without_selected_attribute(self, mock_menu_pool):
        """Test node without selected attribute uses False as default"""
        child_node = Mock()
        child_node.visible = True
        child_node.get_menu_title.return_value = "Child"
        child_node.get_absolute_url.return_value = "/child/"
        # Remove selected attribute
        delattr(child_node, "selected")
        delattr(child_node, "indicator")

        home_node = Mock()
        home_node.id = "home"
        home_node.children = [child_node]

        mock_renderer = Mock()
        mock_renderer.get_nodes.return_value = [home_node]
        mock_menu_pool.get_renderer.return_value = mock_renderer

        result = react_sidenav_data(self.context)

        assert result[0]["current"] is False
