from .abstract import ContentsTagWebTest, InclusionTagWebTest


class TestList(ContentsTagWebTest):
    library = "list_tags"
    tag = "render_list"
    contents = '{% list_item text="Lorem ipsum" %}'

    def test_render(self):
        self.assertRender()

    def test_contents(self):
        self.assertContents()


class TestListItem(InclusionTagWebTest):
    library = "list_tags"
    tag = "list_item"

    def test_render(self):
        self.assertRender({"text": "Lorem ipsum"})

    def test_text(self):
        self.assertTextContent("h4", "Lorem ipsum", {"text": "Lorem ipsum"})

    def test_description(self):
        self.assertTextContent(
            "p", "Dolor sit", {"text": "Lorem ipsum", "description": "Dolor sit"}
        )

    def test_href(self):
        self.assertNotSelector("a", {"text": "Lorem ipsum", "description": "Dolor sit"})
        a = self.assertSelector(
            "a",
            {
                "text": "Lorem ipsum",
                "description": "Dolor sit",
                "href": "https://www.example.com",
            },
        )
        self.assertEqual(a[0]["href"], "https://www.example.com")
