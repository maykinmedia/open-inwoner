from django.conf import settings

from cms.models import Page, PageContent
from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from djangocms_versioning.constants import PUBLISHED

from open_inwoner.cms.tests.cms_tools import (
    render_all_placeholders,
    render_full_page,
)
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.pdc.models import Category, Organization, Product, Tag

from .analyzers import html_strip, partial_analyzer, synonym_analyzer


@registry.register_document
class ProductDocument(Document):
    name = fields.TextField(
        analyzer="standard",
        search_analyzer=synonym_analyzer,
        fields={
            "raw": fields.KeywordField(),
            "suggest": fields.CompletionField(),
            "partial": fields.TextField(analyzer=partial_analyzer),
        },
    )
    summary = fields.TextField(
        analyzer="standard",
        search_analyzer=synonym_analyzer,
        fields={"partial": fields.TextField(analyzer=partial_analyzer)},
    )
    content = fields.TextField(
        analyzer="standard",
        search_analyzer=synonym_analyzer,
        fields={"partial": fields.TextField(analyzer=partial_analyzer)},
    )
    slug = fields.KeywordField()

    categories = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
            "description": fields.TextField(),
        }
    )
    tags = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
            "type": fields.TextField(attr="type.name"),
        }
    )
    organizations = fields.NestedField(
        properties={
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
            "type": fields.TextField(attr="type.name"),
            "neighbourhood": fields.TextField(attr="neighbourhood.name"),
        }
    )
    keywords = fields.TextField(
        fields={
            "suggest": fields.CompletionField(multi=True),
            "partial": fields.TextField(multi=True, analyzer=partial_analyzer),
        }
    )

    class Index:
        name = settings.ES_INDEX_PRODUCTS

    class Django:
        model = Product
        related_models = [Tag, Organization, Category]

    def get_queryset(self):
        return super(ProductDocument, self).get_queryset().exclude(published=False)

    def get_instances_from_related(self, related_instance):
        return related_instance.products.all()

    def prepare_content(self, instance):
        """Convert ProsemirrorFieldDocument to HTML string for indexing."""
        if hasattr(instance.content, "html"):
            return instance.content.html
        return str(instance.content) if instance.content else ""

    def prepare_categories(self, instance):
        """Prepare categories with description converted to HTML."""
        categories = []
        for category in instance.categories.all():
            category_data = {
                "name": category.name,
                "slug": category.slug,
                "description": "",
            }
            if category.description:
                if hasattr(category.description, "html"):
                    category_data["description"] = category.description.html
                else:
                    category_data["description"] = str(category.description)
            categories.append(category_data)
        return categories


@registry.register_document
class CMSPageDocument(Document):
    title = fields.TextField()
    rendered_html = fields.TextField(analyzer=html_strip)
    rendered_placeholders = fields.TextField(analyzer=html_strip)
    description = fields.TextField()
    url = fields.TextField()

    def prepare_description(self, instance: Page):
        return instance.get_meta_description(fallback=False, language="nl")

    def prepare_rendered_html(self, instance: Page):
        content = render_full_page(instance)
        return content

    def prepare_rendered_placeholders(self, instance: Page):
        content = render_all_placeholders(instance)
        return content

    def prepare_title(self, instance: Page):
        # The __str__ method for a page returns the title
        return str(instance)

    def prepare_url(self, instance: Page):
        return instance.get_absolute_url() or ""

    def get_queryset(self):
        site_config = SiteConfiguration.get_solo()
        if not site_config.include_cms_pages_in_search_index:
            return Page.objects.none()

        published_page_ids = PageContent._original_manager.filter(
            versions__state=PUBLISHED
        ).values_list("page_id", flat=True)
        return Page.objects.filter(id__in=published_page_ids)

    class Index:
        name = settings.ES_INDEX_CMS_PAGES

    class Django:
        model = Page
        auto_refresh = False
        ignore_signals = True
