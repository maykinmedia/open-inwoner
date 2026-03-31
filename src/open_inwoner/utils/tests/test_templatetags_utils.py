from django.test import TestCase

from django_prosemirror.config import ProsemirrorConfig
from django_prosemirror.serde import doc_to_html

from open_inwoner.utils.templatetags.utils import prosemirror_html_to_markdown

# Maps a descriptive name to (ProseMirror HTML input, expected rendered HTML output).
# Tested via assertHTMLEqual (whitespace-insensitive structural comparison).
HTML_TO_MARKDOWN_SPEC = {
    # --- Nodes: Headings (ATX-style) ---
    "h1_atx": ("<p># Heyy</p>", "<h1>Heyy</h1>"),
    "h2_atx": ("<p>## Subtitle</p>", "<h2>Subtitle</h2>"),
    "h3_atx": ("<p>### Sub</p>", "<h3>Sub</h3>"),
    "h4_atx": ("<p>#### Sub</p>", "<h4>Sub</h4>"),
    "h5_atx": ("<p>##### Sub</p>", "<h5>Sub</h5>"),
    "h6_atx": ("<p>###### Sub</p>", "<h6>Sub</h6>"),
    # Setext-style headings
    "h1_setext": (
        "<p>Heading level 1\n===============</p>",
        "<h1>Heading level 1</h1>",
    ),
    "h2_setext": (
        "<p>Heading level 2\n---------------</p>",
        "<h2>Heading level 2</h2>",
    ),
    # --- Nodes: Paragraph ---
    "paragraph": ("<p>Hello world</p>", "<p>Hello world</p>"),
    # --- Nodes: Horizontal rules ---
    "hr_dashes": ("<p>---</p>", "<hr />"),
    "hr_asterisks": ("<p>***</p>", "<hr />"),
    "hr_underscores": ("<p>___</p>", "<hr />"),
    # --- Nodes: Line breaks ---
    # Two trailing spaces produce a <br>
    "br_trailing_spaces": (
        "<p>First line.  \nSecond line.</p>",
        "<p>First line.<br />\nSecond line.</p>",
    ),
    # A <br> inside a <p> becomes two separate paragraphs after get_text("\n\n")
    "br_html_tag": (
        "<p>First line.<br>Second line.</p>",
        "<p>First line.</p><p>Second line.</p>",
    ),
    # --- Nodes: Blockquotes ---
    "blockquote_basic": (
        "<p>&gt; Blockquote text</p>",
        "<blockquote><p>Blockquote text</p></blockquote>",
    ),
    # Nested blockquote (no space between markers)
    "blockquote_nested_2": (
        "<p>&gt;&gt; nested quote</p>",
        "<blockquote><blockquote><p>nested quote</p></blockquote></blockquote>",
    ),
    # Nested blockquote (four levels, space-separated markers)
    "blockquote_nested_4": (
        "<p>&gt; &gt; &gt; &gt; nested quote</p>",
        "<blockquote><blockquote><blockquote><blockquote>"
        "<p>nested quote</p>"
        "</blockquote></blockquote></blockquote></blockquote>",
    ),
    # Content on the same editor line as > stays inside the blockquote
    "blockquote_inline_content": (
        "<p>&gt; Blockquote _idk_</p>",
        "<blockquote><p>Blockquote <em>idk</em></p></blockquote>",
    ),
    # A separate <p> after a blockquote must not be absorbed into it
    "blockquote_separate_paragraph_after": (
        "<p>&gt; Blockquote</p><p>_outside_</p>",
        "<blockquote><p>Blockquote</p></blockquote><p><em>outside</em></p>",
    ),
    # > on blank lines between paragraphs keeps them inside the blockquote
    "blockquote_multi_paragraph": (
        "<p>&gt; First paragraph.</p><p>&gt;</p><p>&gt; Second paragraph.</p>",
        "<blockquote><p>First paragraph.</p><p>Second paragraph.</p></blockquote>",
    ),
    "blockquote_with_heading": (
        "<p>&gt; #### The quarterly results</p>",
        "<blockquote><h4>The quarterly results</h4></blockquote>",
    ),
    "blockquote_with_list_and_emphasis": (
        "<p>&gt; - Revenue was off the chart.</p>"
        "<p>&gt; - Profits were higher than ever.</p>"
        "<p>&gt; *Everything* is going according to **plan**.</p>",
        """
        <blockquote>
            <ul>
                <li><p>Revenue was off the chart.</p></li>
                <li><p>Profits were higher than ever.</p></li>
            </ul>
            <p><em>Everything</em> is going according to <strong>plan</strong>.</p>
        </blockquote>
        """,
    ),
    # --- Nodes: Lists ---
    # Separate <p> tags → loose list → <li><p>text</p></li>
    "ordered_list": (
        "<p>1. first</p><p>2. second</p>",
        "<ol><li><p>first</p></li><li><p>second</p></li></ol>",
    ),
    "unordered_list_dash": (
        "<p>- first</p><p>- second</p>",
        "<ul><li><p>first</p></li><li><p>second</p></li></ul>",
    ),
    "unordered_list_star": (
        "<p>* first</p><p>* second</p>",
        "<ul><li><p>first</p></li><li><p>second</p></li></ul>",
    ),
    "unordered_list_plus": (
        "<p>+ first</p><p>+ second</p>",
        "<ul><li><p>first</p></li><li><p>second</p></li></ul>",
    ),
    "list_after_blockquote_is_outside": (
        "<p>&gt; Blockquote</p><p>1. item</p>",
        "<blockquote><p>Blockquote</p></blockquote><ol><li>item</li></ol>",
    ),
    # 1. 1. 1. still produces a sequential list
    "ordered_list_all_same_number": (
        "<p>1. first</p><p>1. second</p><p>1. third</p>",
        "<ol><li><p>first</p></li><li><p>second</p></li><li><p>third</p></li></ol>",
    ),
    # 1968\. renders as literal "1968." inside a list item, not a new ordered list
    "unordered_list_item_starting_with_number_escaped": (
        "<p>- 1968\\. A great year!</p><p>- I think 1969 was second best.</p>",
        """
        <ul>
            <li><p>1968. A great year!</p></li>
            <li><p>I think 1969 was second best.</p></li>
        </ul>
        """,
    ),
    # Nested ordered list
    "nested_ordered_list": (
        "<p>1. parent</p><p>    1. child one</p><p>    2. child two</p>",
        """
        <ol>
            <li>
                <p>parent</p>
                <ol>
                    <li><p>child one</p></li>
                    <li><p>child two</p></li>
                </ol>
            </li>
        </ol>
        """,
    ),
    # ul nested inside ol
    "mixed_nested_list_ul_inside_ol": (
        "<p>1. First item</p>"
        "<p>2. Second item</p>"
        "<p>3. Third item</p>"
        "<p>    - Indented item</p>"
        "<p>    - Indented item</p>"
        "<p>4. Fourth item</p>",
        """
        <ol>
            <li><p>First item</p></li>
            <li><p>Second item</p></li>
            <li>
                <p>Third item</p>
                <ul>
                    <li><p>Indented item</p></li>
                    <li><p>Indented item</p></li>
                </ul>
            </li>
            <li><p>Fourth item</p></li>
        </ol>
        """,
    ),
    # --- Nodes: Code ---
    "fenced_code_block": (
        "<p>```</p><p>code here</p><p>```</p>",
        "<pre><code>\ncode here\n\n</code></pre>",
    ),
    # Four-space-indented lines produce an indented code block
    "indented_code_block": (
        "<p>    &lt;html&gt;</p><p>    &lt;/html&gt;</p>",
        "<pre><code>&lt;html&gt;\n\n&lt;/html&gt;\n</code></pre>",
    ),
    # --- Nodes: Misc ---
    # ProseMirror emits <p><br></p> for blank lines; must not break rendering
    "empty_paragraph_br": (
        "<p># Heading</p><p><br></p><p>paragraph</p>",
        "<h1>Heading</h1><p>paragraph</p>",
    ),
    # --- Marks ---
    "bold_double_asterisk": (
        "<p>**bold text**</p>",
        "<p><strong>bold text</strong></p>",
    ),
    "bold_double_underscore": (
        "<p>__bold text__</p>",
        "<p><strong>bold text</strong></p>",
    ),
    "italic_underscore": ("<p>_italic_</p>", "<p><em>italic</em></p>"),
    "italic_star": ("<p>*italic*</p>", "<p><em>italic</em></p>"),
    "inline_code": ("<p>`code`</p>", "<p><code>code</code></p>"),
    # <u> is stripped by get_text(); only text survives (no markdown for underline)
    "underline_html_tag_text_preserved": (
        "<p><u>underline</u></p>",
        "<p>underline</p>",
    ),
    "bold_italic_triple_asterisk": (
        "<p>***really important***</p>",
        "<p><strong><em>really important</em></strong></p>",
    ),
    "bold_italic_triple_underscore": (
        "<p>___really important___</p>",
        "<p><strong><em>really important</em></strong></p>",
    ),
    "mixed_inline_marks": (
        "<p>**bold** and _italic_ and `code`</p>",
        "<p><strong>bold</strong> and <em>italic</em> and <code>code</code></p>",
    ),
    # Double-backtick span allows a literal backtick inside
    "escaped_backtick_with_double_backtick": (
        "<p>``Use `code` in your file.``</p>",
        "<p><code>Use `code` in your file.</code></p>",
    ),
    # Escaped marks
    "escape_asterisk": ("<p>\\* not a list item</p>", "<p>* not a list item</p>"),
    "escape_underscore": ("<p>\\_not italic\\_</p>", "<p>_not italic_</p>"),
    # --- Links ---
    "link": (
        "<p>[click here](https://example.com)</p>",
        '<p><a href="https://example.com">click here</a></p>',
    ),
    "link_with_title": (
        '<p>[click here](https://example.com "My title")</p>',
        '<p><a href="https://example.com" title="My title">click here</a></p>',
    ),
    # <a> tag from ProseMirror: get_text() strips the href, only text is preserved
    "link_as_html_tag_preserves_text": (
        '<p><a href="https://example.com">click here</a></p>',
        "<p>click here</p>",
    ),
    # Auto-links
    "autolink_url": (
        "<p>&lt;https://www.markdownguide.org&gt;</p>",
        '<p><a href="https://www.markdownguide.org">https://www.markdownguide.org</a></p>',
    ),
    # Email auto-link (assertHTMLEqual decodes the entity-obfuscated output)
    "autolink_email": (
        "<p>&lt;fake@example.com&gt;</p>",
        '<p><a href="mailto:fake@example.com">fake@example.com</a></p>',
    ),
    # Reference-style link
    "reference_style_link": (
        "<p>It was a [hobbit-hole][1], and that means comfort.</p>"
        '<p>[1]: https://en.wikipedia.org/wiki/Hobbit#Lifestyle "Hobbit lifestyles"</p>',
        '<p>It was a <a href="https://en.wikipedia.org/wiki/Hobbit#Lifestyle"'
        ' title="Hobbit lifestyles">hobbit-hole</a>, and that means comfort.</p>',
    ),
    "bold_link": (
        "<p>**[EFF](https://eff.org)**</p>",
        '<p><strong><a href="https://eff.org">EFF</a></strong></p>',
    ),
    "italic_link": (
        "<p>*[Markdown Guide](https://www.markdownguide.org)*</p>",
        '<p><em><a href="https://www.markdownguide.org">Markdown Guide</a></em></p>',
    ),
    # --- Images ---
    "image": (
        "<p>![Alt text](/path/to/image.jpg)</p>",
        '<p><img alt="Alt text" src="/path/to/image.jpg"></p>',
    ),
    "image_with_title": (
        '<p>![Alt text](/path/to/image.jpg "Image title")</p>',
        '<p><img alt="Alt text" src="/path/to/image.jpg" title="Image title"></p>',
    ),
    "linked_image": (
        "<p>[![Alt](/img.jpg)](https://example.com)</p>",
        '<p><a href="https://example.com"><img alt="Alt" src="/img.jpg"></a></p>',
    ),
    # --- Extra extensions: Tables ---
    "table_basic": (
        "<p>| A | B |</p><p>| --- | --- |</p><p>| 1 | 2 |</p>",
        """
        <table>
            <thead><tr><th>A</th><th>B</th></tr></thead>
            <tbody><tr><td>1</td><td>2</td></tr></tbody>
        </table>
        """,
    ),
    # attr_list on td (space before {}) applies class to td;
    # attr_list directly on the mark (no space) applies class to the mark element
    "table_with_attr_list": (
        "<p>| set on td    | set on em   |</p>\n"
        "<p>|--------------|-------------|</p>\n"
        "<p>| *a* { .foo } | *b*{ .foo } |</p>",
        """
        <table>
          <thead>
            <tr>
              <th>set on td</th>
              <th>set on em</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="foo"><em>a</em></td>
              <td><em class="foo">b</em></td>
            </tr>
          </tbody>
        </table>
        """,
    ),
    # --- Extra extensions: Footnotes ---
    "footnote": (
        "<p>Word[^1].</p><p>[^1]: The footnote.</p>",
        """
        <p>Word<sup id="fnref:1"><a class="footnote-ref" href="#fn:1">1</a></sup>.</p>
        <div class="footnote">
            <hr>
            <ol>
                <li id="fn:1">
                    <p>The footnote.&#160;<a class="footnote-backref" href="#fnref:1"
                        title="Jump back to footnote 1 in the text">&#8617;</a></p>
                </li>
            </ol>
        </div>
        """,
    ),
    # --- Extra extensions: Definition list ---
    "definition_list": (
        "<p>Apple</p><p>: A fruit</p>",
        "<dl>\n<dt>Apple</dt>\n<dd>\n<p>A fruit</p>\n</dd>\n</dl>",
    ),
    # --- Extra extensions: Abbreviation ---
    "abbreviation": (
        "<p>The HTML spec.</p><p>*[HTML]: Hyper Text Markup Language</p>",
        '<p>The <abbr title="Hyper Text Markup Language">HTML</abbr> spec.</p>',
    ),
    # --- Extra extensions: Attribute list ---
    "attr_list_heading_id": (
        "<p>## My Heading { #custom-id }</p>",
        '<h2 id="custom-id">My Heading</h2>',
    ),
    # --- Sane lists ---
    # Ordered then unordered separated by a blank line → two distinct lists
    "sane_lists_mixed_types_produce_separate_lists": (
        "<p>1. Ordered item 1</p>"
        "<p>2. Ordered item 2</p>"
        "<p><br></p>"
        "<p>* Unordered item 1</p>"
        "<p>* Unordered item 2</p>",
        """
        <ol>
            <li><p>Ordered item 1</p></li>
            <li><p>Ordered item 2</p></li>
        </ol>
        <ul>
            <li><p>Unordered item 1</p></li>
            <li><p>Unordered item 2</p></li>
        </ul>
        """,
    ),
    # Without a blank line, a different marker is continuation text, not a new list
    "sane_lists_no_blank_line_mixed_type_ignored": (
        "<p>1. Ordered list item.\n* Not a separate list item.</p>",
        "<ol><li>Ordered list item.\n* Not a separate list item.</li></ol>",
    ),
    # sane_lists preserves the starting number of an ordered list
    "sane_lists_preserves_start_number": (
        "<p>4. Apples</p><p>5. Oranges</p><p>6. Pears</p>",
        '<ol start="4"><li><p>Apples</p></li><li><p>Oranges</p></li><li><p>Pears</p></li></ol>',
    ),
    # --- Full document ---
    "full_document": (
        "<p># Heading 1</p>"
        "<p>## Heading 2</p>"
        "<p>### Heading 3</p>"
        "<p>A plain paragraph with **bold**, _italic_, __also bold__, "
        "***bold and italic***, and `inline code`.</p>"
        "<p>---</p>"
        "<p>&gt; #### Blockquote heading</p>"
        "<p>&gt;</p>"
        "<p>&gt; *Everything* is going according to **plan**.</p>"
        "<p>&gt;&gt; Nested blockquote</p>"
        "<p>1. First item</p>"
        "<p>2. Second item</p>"
        "<p>3. Third item</p>"
        "<p>    - Indented unordered</p>"
        "<p>    - Indented unordered 2</p>"
        "<p>4. Fourth item</p>"
        "<p>- Alpha</p>"
        "<p>- Beta</p>"
        "<p>    1. nested one</p>"
        "<p>    2. nested two</p>"
        "<p>- Gamma</p>"
        "<p>```python</p>"
        "<p>print('hello')</p>"
        "<p>```</p>"
        '<p>Visit [Duck Duck Go](https://duckduckgo.com "Best search engine").</p>'
        '<p>![Logo](/logo.png "Site logo")</p>'
        "<p>&lt;https://www.example.com&gt;</p>"
        "<p>\\* not a list item</p>",
        """
        <h1>Heading 1</h1>
        <h2>Heading 2</h2>
        <h3>Heading 3</h3>
        <p>A plain paragraph with <strong>bold</strong>, <em>italic</em>,
           <strong>also bold</strong>, <strong><em>bold and italic</em></strong>,
           and <code>inline code</code>.</p>
        <hr>
        <blockquote>
            <h4>Blockquote heading</h4>
            <p><em>Everything</em> is going according to <strong>plan</strong>.</p>
            <blockquote>
                <p>Nested blockquote</p>
            </blockquote>
        </blockquote>
        <ol>
            <li><p>First item</p></li>
            <li><p>Second item</p></li>
            <li>
                <p>Third item</p>
                <ul>
                    <li><p>Indented unordered</p></li>
                    <li><p>Indented unordered 2</p></li>
                </ul>
            </li>
            <li><p>Fourth item</p></li>
        </ol>
        <ul>
            <li><p>Alpha</p></li>
            <li>
                <p>Beta</p>
                <ol>
                    <li><p>nested one</p></li>
                    <li><p>nested two</p></li>
                </ol>
            </li>
            <li><p>Gamma</p></li>
        </ul>
        <pre><code class="language-python">print('hello')
</code></pre>
        <p>Visit <a href="https://duckduckgo.com" title="Best search engine">Duck Duck Go</a>.</p>
        <p><img src="/logo.png" alt="Logo" title="Site logo"></p>
        <p><a href="https://www.example.com">https://www.example.com</a></p>
        <p>* not a list item</p>
        """,
    ),
}


class ProsemirrorHtmlToMarkdownFilterTest(TestCase):
    """
    The `prosemirror_html_to_markdown` filter receives ProseMirror HTML where the
    user has typed raw markdown syntax.  ProseMirror wraps each paragraph in a <p>
    tag, so the input looks like:  <p># Heading</p><p>**bold**</p> etc.

    The filter uses BeautifulSoup.get_text("\\n\\n") to extract the markdown text
    with blank-line-separated blocks, then passes it to the markdown parser.
    """

    def test_spec(self):
        for name, (value, expected) in HTML_TO_MARKDOWN_SPEC.items():
            with self.subTest(name):
                self.assertHTMLEqual(prosemirror_html_to_markdown(value), expected)

    def test_full_document_via_doc_to_html(self):
        """
        Same stress test as the "full_document" entry in HTML_TO_MARKDOWN_SPEC, but
        the input HTML is produced by doc_to_html from a real ProseMirror document
        dict.  This catches any change in how the library serialises paragraph nodes
        to HTML (e.g. switching from <p> to <div>) that would silently break the filter.
        """
        schema = ProsemirrorConfig().schema

        def p(text):
            return {"type": "paragraph", "content": [{"type": "text", "text": text}]}

        doc = {
            "type": "doc",
            "content": [
                # Headings h1–h3
                p("# Heading 1"),
                p("## Heading 2"),
                p("### Heading 3"),
                # Paragraph with all inline marks
                p(
                    "A plain paragraph with **bold**, _italic_, __also bold__, "
                    "***bold and italic***, and `inline code`."
                ),
                # Horizontal rule
                p("---"),
                # Blockquote with nested content
                p("> #### Blockquote heading"),
                p(">"),
                p("> *Everything* is going according to **plan**."),
                # Nested blockquote
                p(">> Nested blockquote"),
                # Ordered list with nested unordered list
                p("1. First item"),
                p("2. Second item"),
                p("3. Third item"),
                p("    - Indented unordered"),
                p("    - Indented unordered 2"),
                p("4. Fourth item"),
                # Unordered list with nested ordered list
                p("- Alpha"),
                p("- Beta"),
                p("    1. nested one"),
                p("    2. nested two"),
                p("- Gamma"),
                # Fenced code block
                p("```python"),
                p("print('hello')"),
                p("```"),
                # Link, image, auto-link
                p('Visit [Duck Duck Go](https://duckduckgo.com "Best search engine").'),
                p('![Logo](/logo.png "Site logo")'),
                p("<https://www.example.com>"),
                # Escaped character
                p("\\* not a list item"),
            ],
        }

        _, expected = HTML_TO_MARKDOWN_SPEC["full_document"]
        self.assertHTMLEqual(
            prosemirror_html_to_markdown(doc_to_html(doc, schema=schema)),
            expected,
        )
