from django.contrib.flatpages.models import FlatPage
from django.db import models
from django.utils.translation import ugettext_lazy as _

import markdown
from bs4 import BeautifulSoup
from colorfield.fields import ColorField
from filer.fields.image import FilerImageField
from ordered_model.models import OrderedModel, OrderedModelManager
from solo.models import SingletonModel

from .choices import ColorTypeChoices


class SiteConfiguration(SingletonModel):
    name = models.CharField(max_length=255, help_text=_("The name of the municipality"))
    primary_color = ColorField(
        help_text=_("The primary color of the municipality's site"),
    )
    secondary_color = ColorField(
        help_text=_("The secondary color of the municipality's site"),
    )
    accent_color = ColorField(
        help_text=_("The accent color of the municipality's site"),
    )
    primary_font_color = models.CharField(
        max_length=50,
        choices=ColorTypeChoices.choices,
        default=ColorTypeChoices.light,
        help_text=_("The font color for when the background is the primary color"),
    )
    secondary_font_color = models.CharField(
        max_length=50,
        choices=ColorTypeChoices.choices,
        default=ColorTypeChoices.light,
        help_text=_("The font color for when the background is the secondary color"),
    )
    accent_font_color = models.CharField(
        max_length=50,
        choices=ColorTypeChoices.choices,
        default=ColorTypeChoices.dark,
        help_text=_("The font color for when the background is the accent color"),
    )
    logo = FilerImageField(
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="site_logo",
        help_text=_("Logo of the municipality"),
    )
    hero_image_login = FilerImageField(
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hero_image_login",
        help_text=_("Hero image on the login page"),
    )
    login_allow_registration = models.BooleanField(
        verbose_name=_("Sta lokale registratie toe"),
        default=False,
        help_text=_(
            "Standaard is het enkel toegestraan middels DigiD in te loggen. Zet deze installing aan om ook registraties op website niveau toe te staan."
        ),
    )
    login_text = models.TextField(
        blank=True,
        verbose_name=_("Login tekst"),
        help_text=_("Deze tekst wordt getoond op de login pagina."),
    )
    home_welcome_title = models.CharField(
        max_length=255,
        default=_("Welcom"),
        verbose_name=_("Home welcome title"),
        help_text=_("Welcome title on the home page."),
    )
    home_welcome_intro = models.TextField(
        verbose_name=_("Home welcome intro"),
        blank=True,
        help_text=_("Welcome intro text on the home page."),
    )
    theme_title = models.CharField(
        max_length=255,
        default=_("Thema's"),
        verbose_name=_("Theme's title"),
        help_text=_("Theme's title on the home and theme's page."),
    )
    theme_intro = models.TextField(
        verbose_name=_("Theme's intro"),
        blank=True,
        help_text=_("Theme's intro text on the home and thema's page."),
    )
    home_map_title = models.CharField(
        max_length=255,
        default=_("In de buurt"),
        verbose_name=_("Home map title"),
        help_text=_("Map's title on the home page."),
    )
    home_map_intro = models.TextField(
        verbose_name=_("Home map intro"),
        blank=True,
        help_text=_("Map's intro text on the home page."),
    )
    footer_visitor_mail = models.TextField(
        _("Footer content"),
        blank=True,
        default="",
        help_text=_("Visitor and mailing content with build-in WYSIWYG editor"),
    )
    flatpages = models.ManyToManyField(
        FlatPage, through="SiteConfigurationPage", related_name="configurations"
    )

    class Meta:
        verbose_name = "Site Configuration"

    def __str__(self):
        return "Site Configuration"

    @property
    def get_primary_color(self):
        return self.hex_to_hsl(self.primary_color)

    @property
    def get_secondary_color(self):
        return self.hex_to_hsl(self.secondary_color)

    @property
    def get_accent_color(self):
        return self.hex_to_hsl(self.accent_color)

    def hex_to_hsl(self, color):
        # Convert hex to RGB first
        r = 0
        g = 0
        b = 0
        if len(color) == 4:
            r = "0x" + color[1] + color[1]
            g = "0x" + color[2] + color[2]
            b = "0x" + color[3] + color[3]
        elif len(color) == 7:
            r = "0x" + color[1] + color[2]
            g = "0x" + color[3] + color[4]
            b = "0x" + color[5] + color[6]

        # Then to HSL
        r = int(r, 16) / 255
        g = int(g, 16) / 255
        b = int(b, 16) / 255
        cmin = min(r, g, b)
        cmax = max(r, g, b)
        delta = cmax - cmin
        h = 0
        s = 0
        l = 0

        if delta == 0:
            h = 0
        elif cmax == r:
            h = ((g - b) / delta) % 6
        elif cmax == g:
            h = (b - r) / delta + 2
        else:
            h = (r - g) / delta + 4

        h = round(h * 60)

        if h < 0:
            h += 360

        l = (cmax + cmin) / 2
        s = 0 if delta == 0 else delta / (1 - abs(2 * l - 1))
        s = int((s * 100))
        l = int((l * 100))

        return h, s, l

    def get_rendered_content(self):
        md = markdown.Markdown()
        html = md.convert(self.footer_visitor_mail)
        soup = BeautifulSoup(html, "html.parser")
        class_adders = [
            ("h1", "h1"),
            ("h2", "h2"),
            ("h3", "h3"),
            ("h4", "h4"),
            ("h5", "h5"),
            ("h6", "h6"),
            ("p", "p"),
            ("a", "link"),
        ]
        for tag, class_name in class_adders:
            for element in soup.find_all(tag):
                element.attrs["class"] = class_name

        return soup


class SiteConfigurationPage(OrderedModel):
    configuration = models.ForeignKey(SiteConfiguration, on_delete=models.CASCADE)
    flatpage = models.ForeignKey(FlatPage, on_delete=models.CASCADE)
    order_with_respect_to = "configuration"

    objects = OrderedModelManager()

    def __str__(self):
        return self.flatpage.title

    @property
    def page_nr(self):
        return self.order + 1
