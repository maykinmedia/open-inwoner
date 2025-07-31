from unittest.mock import patch

from django.test.client import RequestFactory

from cms.api import add_plugin, create_page
from cms.plugin_rendering import ContentRenderer
from cms.test_utils.testcases import CMSTestCase

from ..models import Theme as ThemeModel, ThemeList as ThemeListModel


class ThemeTestCase(CMSTestCase):
    def setUp(self):
        self.page = create_page("Themes test Page", "cms/fullwidth.html", "nl")
        self.placeholder = self.page.placeholders.get(slot="content")

        self.my_parking_page = create_page(
            "Mijn parkeren", "cms/fullwidth.html", "nl", slug="mijn-parkeren"
        )

    def test_theme_list_plugin_renders(self):
        theme_list = ThemeListModel.objects.create(title="Mijn documenten")
        theme_list_plugin_instance = add_plugin(
            self.placeholder, "ThemeListPlugin", "nl", title=theme_list.title
        )

        self.assertIsNotNone(theme_list_plugin_instance)
        self.assertEqual(theme_list_plugin_instance.title, "Mijn documenten")

        plugins = self.placeholder.get_plugins()
        self.assertEqual(len(plugins), 1)

        plugin_instance = plugins[0].get_plugin_instance()[0]
        self.assertEqual(plugin_instance.title, "Mijn documenten")

        plugin_instance = theme_list_plugin_instance.get_plugin_class_instance()
        context = plugin_instance.render({}, theme_list_plugin_instance, None)
        self.assertEqual("Mijn documenten", context["instance"].title)

    def test_theme_plugin_renders(self):
        # Obtain a theme list first, as it is the parent of Theme
        theme_list = ThemeListModel.objects.create(title="Mijn documenten")
        theme_list_plugin_instance = add_plugin(
            self.placeholder, "ThemeListPlugin", "nl", title=theme_list.title
        )

        theme = ThemeModel.objects.create(
            title="Mijn parkeren",
            caption="Example caption",
            required_actions=False,
            theme_page=self.my_parking_page,
        )

        theme_plugin_instance = add_plugin(
            self.placeholder,
            "ThemePlugin",
            "nl",
            parent=theme_list_plugin_instance,
            title=theme.title,
            caption=theme.caption,
            required_actions=theme.required_actions,
            theme_page=theme.theme_page,
        )

        self.assertIsNotNone(theme_plugin_instance)
        self.assertEqual(theme_plugin_instance.title, "Mijn parkeren")

        with patch.object(
            self.my_parking_page, "get_absolute_url", return_value="/mijn-parkeren/"
        ):
            plugin_instance = theme_plugin_instance.get_plugin_class_instance()

            # Verify context
            context = plugin_instance.render({}, theme_plugin_instance, None)
            self.assertIsNotNone(context["page_url"])
            self.assertIn("/mijn-parkeren/", context["page_url"])

            # Verify rendering
            renderer = ContentRenderer(request=RequestFactory())
            html = renderer.render_plugin(
                theme_plugin_instance,
                {},
            )
            self.assertIn("/mijn-parkeren/", html)
