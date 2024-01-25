from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from django_better_admin_arrayfield.models.fields import ArrayField
from filer.fields.image import FilerImageField
from treebeard.exceptions import InvalidMoveToDescendant
from treebeard.mp_tree import MP_MoveHandler, MP_Node

from ...utils.ckeditor import get_rendered_content
from ..managers import CategoryPublishedQueryset


class PublishedMoveHandler(MP_MoveHandler):
    def process(self):
        if self.node.published and not self.target.published:
            raise InvalidMoveToDescendant(
                _("Published nodes cannot be moved to unpublished ones.")
            )
        return super().process()


class Category(MP_Node):
    name = models.CharField(
        verbose_name=_("Name"), max_length=100, help_text=_("Name of the category")
    )
    slug = models.SlugField(
        verbose_name=_("Slug"),
        max_length=100,
        unique=True,
        help_text=_("Slug of the category"),
    )
    published = models.BooleanField(
        verbose_name=_("Published"),
        default=False,
        help_text=_("Whether the category should be published or not."),
    )
    visible_for_anonymous = models.BooleanField(
        verbose_name=_("Anonieme deel"),
        default=True,
        help_text=_(
            "Of het onderwerp zichtbaar moet zijn op het anonieme deel (zonder inloggen)."
        ),
    )
    visible_for_companies = models.BooleanField(
        verbose_name=_("Bedrijven content"),
        default=True,
        help_text=_(
            "Of het onderwerp zichtbaar moet zijn wanneer iemand aangeeft een bedrijf te zijn (of is ingelogd met KvK)."
        ),
    )
    visible_for_citizens = models.BooleanField(
        verbose_name=_("Inwoner content"),
        default=True,
        help_text=_(
            "Of het onderwerp zichtbaar moet zijn wanneer iemand aangeeft een inwoner te zijn (of is ingelogd met BSN)."
        ),
    )
    zaaktypen = ArrayField(
        models.CharField(max_length=1000, blank=True),
        verbose_name=_("Zaaktypen"),
        default=list,
        blank=True,
        help_text=_(
            "Zaaktypen waarvoor bij aanwezigheid dit onderwerp getoond moet worden."
        ),
    )
    highlighted = models.BooleanField(
        verbose_name=_("Highlighted"),
        default=False,
        help_text=_("Whether the category should be highlighted or not"),
    )
    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        default="",
        help_text=_("Description of the category"),
    )
    icon = FilerImageField(
        verbose_name=_("Icon"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_icons",
        help_text=_("Icon of the category"),
    )
    image = FilerImageField(
        verbose_name=_("Image"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_images",
        help_text=_("Image of the category"),
    )

    auto_redirect_to_link = models.URLField(
        verbose_name=_("Automatically redirect to link"),
        max_length=1000,
        blank=True,
        default="",
        help_text=_(
            "If configured, the user will be automatically redirected to this link "
            "when accessing the category detail page."
        ),
    )

    access_groups = models.ManyToManyField(
        "auth.Group",
        verbose_name=_("Restrict to admin groups"),
        blank=True,
        help_text=_(
            "If set, only users belonging to this group can edit this category and its products"
        ),
        related_name="managed_categories",
    )

    objects = CategoryPublishedQueryset.as_manager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ("path",)

    def __str__(self):
        return self.name

    def get_build_slug(self):
        if self.is_root():
            build_slug = self.slug
        else:
            build_slug = "/".join(
                list(self.get_ancestors().values_list("slug", flat=True))
            )
            build_slug += f"/{self.slug}"
        return build_slug

    def get_absolute_url(self):
        return reverse(
            "products:category_detail", kwargs={"slug": self.get_build_slug()}
        )

    def move(self, target, pos=None):
        return PublishedMoveHandler(self, target, pos).process()
