import logging  # noqa: TID251 - keep for old migrations
import re
from html.parser import HTMLParser

from django.conf import settings

logger = logging.getLogger(__name__)


class _TextExtractor(HTMLParser):
    """Extract text content from HTML."""

    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)

    def get_text(self):
        return "".join(self.text)


def _has_text_content(html):
    """
    Check if HTML has actual text content (not just tags/whitespace).

    Returns:
        bool: True if HTML contains non-whitespace text, False otherwise
    """
    extractor = _TextExtractor()
    extractor.feed(html)
    text = extractor.get_text().strip()
    return bool(text)


def create_text_fallback_prosemirror_doc(html_content):
    """
    Create a valid Prosemirror document with stringified content.
    Used when HTML parsing fails.

    Args:
        html_content: HTML string to extract text from

    Returns:
        dict: Valid Prosemirror document with text content in paragraphs
    """
    extractor = _TextExtractor()
    try:
        extractor.feed(html_content)
        text = extractor.get_text().strip()
    except Exception:
        text = str(html_content)

    if not text:
        return {"type": "doc", "content": [{"type": "paragraph"}]}

    # Split into paragraphs by newlines
    paragraphs = []
    for line in text.split("\n"):
        line = line.strip()
        if line:
            paragraphs.append(
                {"type": "paragraph", "content": [{"type": "text", "text": line}]}
            )

    if not paragraphs:
        paragraphs = [{"type": "paragraph"}]

    return {"type": "doc", "content": paragraphs}


def migrate_to_prosemirror_field(
    apps,
    schema_editor,
    app_label,
    model_name,
    field_name,
    *,
    allowed_node_types=None,
    allowed_mark_types=None,
    use_singleton=False,
    convert_markdown=False,
    strip_quotes=False,
    process_images=False,
    wrap_paragraph=True,
):
    """
    Generic helper to migrate text/HTML fields to ProsemirrorModelField.

    Uses ``.values()`` for reads and ``.update()`` for writes to bypass the
    ProseMirror field descriptor, which raises on non-JSON values in newer
    versions of django-prosemirror.

    Args:
        apps: Django apps registry from migration
        schema_editor: Django schema editor
        app_label: App label (e.g., "configurations", "pdc")
        model_name: Model name (e.g., "SiteConfiguration", "Product")
        field_name: Name of the field being migrated
        allowed_node_types: List of NodeType enums (default: [NodeType.PARAGRAPH])
        allowed_mark_types: List of MarkType enums (default: [STRONG, ITALIC, LINK, UNDERLINE])
        use_singleton: If True, only process the first row
        convert_markdown: If True, convert markdown to HTML before processing
        strip_quotes: If True, strip surrounding quotes from content
        process_images: If True, process filer_image nodes to add imageId attributes
        wrap_paragraph: If True, wrap content in <p> tags if not already wrapped

    Note:
        Dependencies are imported inside the function to ensure migration files referencing
        `ProsemirrorModelField` can be loaded even if the dependencies should be removed
        at a later stage (the migrations will be skipped, but Django needs to load and
        inspect the file in order to know which migrations have already been applied)

    Example:
        >>> from functools import partial
        >>> from open_inwoner.utils.migration_operations import migrate_to_prosemirror_field
        >>> from django_prosemirror.schema import NodeType, MarkType
        >>>
        >>> # Simple case: singleton config with HTML content
        >>> migrate_login_text = partial(
        ...     migrate_to_prosemirror_field,
        ...     app_label="configurations",
        ...     model_name="SiteConfiguration",
        ...     field_name="login_text",
        ...     use_singleton=True,
        ... )
        >>>
        >>> # With markdown conversion
        >>> migrate_description = partial(
        ...     migrate_to_prosemirror_field,
        ...     app_label="ssd",
        ...     model_name="SSDConfig",
        ...     field_name="jaaropgave_display_text",
        ...     use_singleton=True,
        ...     convert_markdown=True,
        ... )
        >>>
        >>> # With images and headings
        >>> migrate_product_content = partial(
        ...     migrate_to_prosemirror_field,
        ...     app_label="pdc",
        ...     model_name="Product",
        ...     field_name="content",
        ...     allowed_node_types=[NodeType.HARD_BREAK, NodeType.PARAGRAPH, NodeType.HEADING, NodeType.FILER_IMAGE],
        ...     use_singleton=False,
        ...     convert_markdown=True,
        ...     process_images=True,
        ... )
    """
    import markdown
    from django_prosemirror.config import ProsemirrorConfig
    from django_prosemirror.schema import MarkType, NodeType
    from django_prosemirror.serde import html_to_doc

    logger = logging.getLogger(__name__)

    if allowed_node_types is None:
        allowed_node_types = [NodeType.HARD_BREAK, NodeType.PARAGRAPH]

    if allowed_mark_types is None:
        allowed_mark_types = [
            MarkType.STRONG,
            MarkType.ITALIC,
            MarkType.LINK,
            MarkType.UNDERLINE,
        ]

    config = ProsemirrorConfig(
        allowed_node_types=allowed_node_types,
        allowed_mark_types=allowed_mark_types,
    )

    Model = apps.get_model(app_label, model_name)
    tmp_col = f"{field_name}_tmp"

    qs = Model.objects.values("pk", tmp_col)
    if use_singleton and qs.exists():
        qs = qs[:1]

    for row in qs:
        pk_value = row["pk"]
        content = row[tmp_col]

        if not content:
            continue

        if convert_markdown:
            content = markdown.markdown(content, extensions=["extra"])

        if not _has_text_content(content):
            logger.info(
                "Skipping %s.%s for pk=%s: no text content",
                model_name,
                field_name,
                pk_value,
            )
            continue

        content = _clean_empty_html_tags(content)

        if not content or not content.strip():
            continue

        try:
            if strip_quotes:
                content = content.strip('"')

            if wrap_paragraph:
                content = content.strip()
                if not content.startswith("<p"):
                    content = f"<p>{content}</p>"

            doc = None
            try:
                doc = html_to_doc(content, schema=config.schema)
            except Exception:
                doc = create_text_fallback_prosemirror_doc(content)
            else:
                if process_images:
                    doc = _add_image_ids_to_prosemirror_doc(doc, apps)

            if doc:
                Model.objects.filter(pk=pk_value).update(**{field_name: doc})

        except Exception as exc:
            logger.warning(
                "Could not convert %s.%s for pk=%s: %s",
                model_name,
                field_name,
                pk_value,
                exc,
            )


def _clean_empty_html_tags(html):
    """
    Remove empty HTML tags to prevent prosemirror parser errors.

    The prosemirror Python library throws IndexError on empty tags like:
    - <p></p>
    - <strong />
    - <p><em></em></p>

    Args:
        html: HTML string to clean

    Returns:
        str: HTML with empty tags removed
    """
    # Replace self-closing tags with proper closing tags
    # <tag /> -> <tag></tag>
    html = re.sub(r"<(\w+)\s*/>", r"<\1></\1>", html)

    # Remove empty tags iteratively (nested empty tags need multiple passes)
    # Matches: <tag></tag> or <tag> </tag> or <tag attrs></tag>
    prev = None
    max_iterations = (
        50  # Safety limit for regex edge cases + malformed HTML to prevent loop
    )
    iteration = 0

    while prev != html and iteration < max_iterations:
        prev = html
        # Remove tags with no content or only whitespace
        html = re.sub(r"<(\w+)(?:\s+[^>]*)?>(\s*)</\1>", "", html)
        iteration += 1

    return html


def _add_image_ids_to_prosemirror_doc(doc, apps):
    """
    Walk through ProseMirror document and add imageId to filer_image nodes.

    html_to_doc converts <img> tags to filer_image nodes, but doesn't set imageId.
    We need to look up the image by URL to get the correct ID.
    """
    import logging  # noqa: TID251 - keep for old migrations

    logger = logging.getLogger(__name__)

    Image = apps.get_model("filer", "Image")

    def process_content(content):
        for node in content:
            if node.get("type") == "filer_image":
                attrs = node.get("attrs", {})
                src = attrs.get("src", "")

                if "imageId" not in attrs and src.startswith(settings.MEDIA_URL):
                    try:
                        # Strip /media/ prefix to get file path
                        file_path = src[len(settings.MEDIA_URL) :]

                        image = Image.objects.get(file=file_path)
                        attrs["imageId"] = str(image.id)

                        # Enhance alt text if empty
                        if not attrs.get("alt"):
                            attrs["alt"] = getattr(image, "default_alt_text", "") or ""

                        # Set default values for other required attrs
                        attrs.setdefault("title", None)
                        attrs.setdefault("caption", "")

                        logger.info("Added imageId %s for URL: %s", image.id, src)
                    except Image.DoesNotExist:
                        logger.warning("Image not found in database for URL: %s", src)
                    except Image.MultipleObjectsReturned:
                        logger.warning("Multiple images found for URL: %s", src)
                    except Exception as e:
                        logger.warning("Error looking up image for URL %s: %s", src, e)

            # Recursively process nested content for all nodes
            if "content" in node:
                process_content(node["content"])

    if "content" in doc:
        process_content(doc["content"])

    return doc
