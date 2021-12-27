from open_inwoner.components.tests.abstract import InclusionTagWebTest


class TestListItem(InclusionTagWebTest):
    library = "querystring_tags"
    tag = "querystring"

    def test_render(self):
        self.assertRender({"key": "lorem", "value": "ipsum"})

    def test_key_value(self):
        html = self.render({"key": "lorem", "value": "ipsum"})
        self.assertEqual("lorem=ipsum", html)

    def test_existing_querystring(self):
        html = self.render({"key": "lorem", "value": "ipsum"}, {"foo": "bar"})
        self.assertEqual("foo=bar&lorem=ipsum", html)

    def test_urlencode(self):
        html = self.render(
            {
                "key": "redirect_to",
                "value": "https://example.com/?email=user@example.com&lorem=ipsum",
            }
        )
        self.assertEqual(
            "redirect_to=https%3A%2F%2Fexample.com%2F%3Femail%3Duser%40example.com%26lorem%3Dipsum",
            html,
        )
