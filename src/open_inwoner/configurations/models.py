import os
from typing import Optional

from django.conf import settings
from django.contrib.flatpages.models import FlatPage
from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from colorfield.fields import ColorField
from django_better_admin_arrayfield.models.fields import ArrayField
from filer.fields.image import FilerImageField
from ordered_model.models import OrderedModel, OrderedModelManager
from solo.models import SingletonModel

from ..utils.colors import hex_to_hsl
from ..utils.css import clean_stylesheet
from ..utils.fields import CSSField
from ..utils.files import OverwriteStorage
from ..utils.validators import FilerExactImageSizeValidator
from .choices import ColorTypeChoices, CustomFontName, OpenIDDisplayChoices
from .validators import validate_oidc_config


class SiteConfiguration(SingletonModel):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
        help_text=_("The name of the municipality"),
    )
    primary_color = ColorField(
        verbose_name=_("Primary color"),
        default="#FFFFFF",
        help_text=_("The primary color of the municipality's site"),
    )
    secondary_color = ColorField(
        verbose_name=_("Secondary color"),
        help_text=_("The secondary color of the municipality's site"),
    )
    accent_color = ColorField(
        verbose_name=_("Accent color"),
        help_text=_("The accent color of the municipality's site"),
    )
    primary_font_color = models.CharField(
        verbose_name=_("Primary font color"),
        max_length=50,
        choices=ColorTypeChoices.choices,
        default=ColorTypeChoices.light,
        help_text=_("The font color for when the background is the primary color"),
    )
    secondary_font_color = models.CharField(
        verbose_name=_("Secondary font color"),
        max_length=50,
        choices=ColorTypeChoices.choices,
        default=ColorTypeChoices.light,
        help_text=_("The font color for when the background is the secondary color"),
    )
    accent_font_color = models.CharField(
        verbose_name=_("Accent font color"),
        max_length=50,
        choices=ColorTypeChoices.choices,
        default=ColorTypeChoices.dark,
        help_text=_("The font color for when the background is the accent color"),
    )
    warning_banner_enabled = models.BooleanField(
        verbose_name=_("Show warning banner"),
        default=False,
        help_text=_("Whether the warning banner should be displayed"),
    )
    warning_banner_text = models.TextField(
        verbose_name=_("Warning banner text"),
        blank=True,
        help_text=_("Text will be displayed on the warning banner"),
    )
    warning_banner_background_color = ColorField(
        verbose_name=_("Warning banner background"),
        default="#FFDBAD",
        help_text=_("The background color for the warning banner"),
    )
    warning_banner_font_color = ColorField(
        verbose_name=_("Warning banner font"),
        default="#000000",
        help_text=_("The font color for the warning banner"),
    )
    logo = FilerImageField(
        verbose_name=_("Logo"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="site_logo",
        help_text=_("Logo of the municipality"),
    )
    hero_image_login = FilerImageField(
        verbose_name=_("Hero image login"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="hero_image_login",
        help_text=_("Deprecated. CMS banner plugin should be used instead."),
    )
    login_show = models.BooleanField(
        verbose_name=_("Toon inlogknop rechts bovenin"),
        default=True,
        help_text=_(
            "Wanneer deze optie uit staat dan kan nog wel worden ingelogd via /accounts/login/ , echter het inloggen is verborgen"
        ),
    )
    login_allow_registration = models.BooleanField(
        verbose_name=_("Sta lokale registratie toe"),
        default=False,
        help_text=_(
            "Wanneer deze optie uit staat is het enkel toegestaan om met DigiD in te loggen. Zet deze instelling aan om ook het inloggen met gebruikersnaam/wachtwoord en het aanmelden zonder DigiD toe te staan."
        ),
    )
    login_2fa_sms = models.BooleanField(
        verbose_name=_("Login with 2FA-with-SMS"),
        default=False,
        help_text=_(
            "Whether we want the users to be able to log in with 2FA authentication by using an SMS workflow."
        ),
    )
    login_text = models.TextField(
        blank=True,
        verbose_name=_("Login tekst"),
        help_text=_("Deze tekst wordt getoond op de login pagina."),
    )
    registration_text = models.TextField(
        blank=True,
        verbose_name=_("Registratie tekst"),
        help_text=_("Deze tekst wordt getoond op de registratie pagina."),
    )
    home_welcome_title = models.CharField(
        max_length=255,
        default=_("Welcome"),
        verbose_name=_("Home welcome title"),
        help_text=_("Welcome title on the home page."),
    )
    home_welcome_intro = models.TextField(
        verbose_name=_("Home welcome intro"),
        blank=True,
        help_text=_("Welcome intro text on the home page."),
    )
    home_theme_title = models.CharField(
        max_length=255,
        default=_("Onderwerpen"),
        verbose_name=_("Home theme's title"),
        help_text=_("Category's title on the home page."),
    )
    home_theme_intro = models.TextField(
        verbose_name=_("Home theme's intro"),
        blank=True,
        help_text=_("Category's intro text on the home page."),
    )
    theme_title = models.CharField(
        max_length=255,
        default=_("Onderwerpen"),
        verbose_name=_("Category's title"),
        help_text=_("Category's title on the theme's page."),
    )
    theme_intro = models.TextField(
        verbose_name=_("Category's intro"),
        blank=True,
        help_text=_("Category's intro text on the theme's page."),
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
    home_questionnaire_title = models.CharField(
        max_length=255,
        default=_("Waar bent u naar op zoek?"),
        verbose_name=_("Home page questionaire title"),
        help_text=_("Questionnaire title on the home page."),
    )
    home_questionnaire_intro = models.TextField(
        default=_("Test met een paar simpele vragen of u recht heeft op een product"),
        verbose_name=_("Home page questionaire intro"),
        blank=True,
        help_text=_("Questionnaire intro text on the home page."),
    )
    home_product_finder_title = models.CharField(
        max_length=255,
        default=_("Productzoeker"),
        verbose_name=_("Product finder title"),
        help_text=_("Product finder's title on the home page."),
    )
    home_product_finder_intro = models.TextField(
        default=_(
            "Met een paar simpele vragen ziet u welke producten passen bij uw situatie"
        ),
        verbose_name=_("Home product finder intro"),
        blank=True,
        help_text=_("Product finder's intro text on the home page."),
    )
    select_questionnaire_title = models.CharField(
        max_length=255,
        default=_("Keuze zelfdiagnose?"),
        verbose_name=_("Questionaire selector widget title"),
        help_text=_("Questionaire selector title on the theme and profile pages."),
    )
    select_questionnaire_intro = models.TextField(
        default=_(
            "Kies hieronder één van de volgende vragenlijsten om de zelfdiagnose te starten."
        ),
        verbose_name=_("Questionaire selector widget intro"),
        blank=True,
        help_text=_("Questionaire selector intro on the theme and profile pages."),
    )
    plans_intro = models.TextField(
        default=_(
            "Hier werkt u aan uw doelen. Dit doet u samen met uw contactpersoon bij de gemeente. "
        ),
        verbose_name=_("Plan pages intro"),
        blank=True,
        help_text=_("The sub-title for the plan page."),
    )
    plans_no_plans_message = models.CharField(
        max_length=255,
        default=_("U heeft nog geen plan gemaakt."),
        verbose_name=_("No plans message"),
        help_text=_("The message in the plans listing when user has no plans."),
    )
    plans_edit_message = models.CharField(
        max_length=255,
        default=_("Hier kunt u uw doel aanpassen"),
        verbose_name=_("Edit goal message"),
        help_text=_("The message when a user edits a goal."),
    )

    footer_logo = FilerImageField(
        verbose_name=_("Footer logo"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="footer_logo",
        help_text=_("Footer logo"),
    )
    footer_logo_title = models.CharField(
        max_length=255,
        default="",
        blank=True,
        verbose_name=_("Footer logo title"),
        help_text=_("The title - help text of the footer logo."),
    )
    footer_logo_url = models.URLField(
        verbose_name=_("Footer logo link"),
        blank=True,
        default="",
        help_text=_("The external link for the footer logo."),
    )
    email_logo = FilerImageField(
        verbose_name=_("Email logo (.png or .jpg)"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="email_logo",
        help_text=_("Image to use as logo in email."),
    )
    favicon = FilerImageField(
        verbose_name=_("Favicon image (32x32, .png)"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="favicon",
        help_text=_("Image to use as favicon"),
        validators=[FilerExactImageSizeValidator(32, 32)],
    )
    flatpages = models.ManyToManyField(
        FlatPage,
        verbose_name=_("Flatpages"),
        through="SiteConfigurationPage",
        related_name="configurations",
    )
    home_help_text = models.TextField(
        blank=True,
        default=_(
            "Welkom! Op dit scherm vindt u een overzicht van de verschillende onderwerpen en producten & diensten."
        ),
        verbose_name=_("Home help"),
        help_text=_("The help text for the home page."),
    )
    theme_help_text = models.TextField(
        blank=True,
        default=_(
            "Op dit scherm vindt u de verschillende onderwerpen waarvoor wij producten en diensten aanbieden."
        ),
        verbose_name=_("Category help"),
        help_text=_("The help text for the theme page."),
    )
    product_help_text = models.TextField(
        blank=True,
        default=_(
            "Op dit scherm kunt u de details vinden over het gekozen product of dienst. Afhankelijk van het product kunt u deze direct aanvragen of meer informatie opvragen."
        ),
        verbose_name=_("Product help"),
        help_text=_("The help text for the product page."),
    )
    search_help_text = models.TextField(
        blank=True,
        default=_("Op dit scherm kunt u zoeken naar de producten en diensten."),
        verbose_name=_("Search help"),
        help_text=_("The help text for the search page."),
    )
    account_help_text = models.TextField(
        blank=True,
        default=_(
            "Op dit scherm ziet u uw persoonlijke profielgegevens en gerelateerde gegevens."
        ),
        verbose_name=_("Account help"),
        help_text=_("The help text for the profile page."),
    )
    questionnaire_help_text = models.TextField(
        blank=True,
        default=_(
            "Het onderdeel Zelfdiagnose stelt u in staat om met het beantwoorden van enkele vragen een advies te krijgen van de gemeente, met concrete vervolgstappen en producten en diensten. U kunt tevens uw antwoorden en het advies bewaren om met een begeleider van de gemeente te bespreken."
        ),
        verbose_name=_("Questionnaire help"),
        help_text=_("The help text for the questionnaire page."),
    )
    plan_help_text = models.TextField(
        blank=True,
        default=_(
            "Met het onderdeel Samenwerken kunt u samen met uw contactpersonen of begeleider van de gemeente aan de slag om met een samenwerkingsplan uw persoonlijke situatie te verbeteren. Door samen aan uw doelen te werken en acties te omschrijven kunnen we elkaar helpen."
        ),
        verbose_name=_("Plan help"),
        help_text=_("The help text for the plan page."),
    )

    # search filters
    search_filter_categories = models.BooleanField(
        verbose_name=_("Add category filter for search results"),
        default=True,
        help_text=_(
            "Whether to show category-checkboxes in order to filter the search result."
        ),
    )
    search_filter_tags = models.BooleanField(
        verbose_name=_("Add tag filter for search results"),
        default=True,
        help_text=_(
            "Whether to show tag-checkboxes in order to filter the search result."
        ),
    )
    search_filter_organizations = models.BooleanField(
        verbose_name=_("Add organization filter for search results"),
        default=True,
        help_text=_(
            "Whether to show organization-checkboxes in order to filter the search result."
        ),
    )

    # email notifications
    email_new_message = models.BooleanField(
        verbose_name=_("Send email about a new message"),
        default=True,
        help_text=_("Whether to send email about each new message the user receives"),
    )
    recipients_email_digest = ArrayField(
        models.EmailField(),
        verbose_name=_("recipients email digest"),
        help_text=_(
            "The email addresses that should receive a daily report of items requiring attention."
        ),
        blank=True,
        default=list,
    )

    # analytics
    gtm_code = models.CharField(
        verbose_name=_("Google Tag Manager code"),
        max_length=50,
        blank=True,
        help_text=_(
            "Typically looks like 'GTM-XXXX'. Supplying this installs Google Tag Manager."
        ),
    )
    ga_code = models.CharField(
        verbose_name=_("Google Analytics code"),
        max_length=50,
        blank=True,
        help_text=_(
            "Typically looks like 'G-XXXXX'. Supplying this installs Google Analytics."
        ),
    )
    matomo_url = models.CharField(
        verbose_name=_("Matomo server URL"),
        max_length=255,
        blank=True,
        help_text=_("The base URL of your Matomo server, e.g. 'matomo.example.com'."),
    )
    matomo_site_id = models.PositiveIntegerField(
        verbose_name=_("Matomo site ID"),
        blank=True,
        null=True,
        help_text=_("The 'idsite' of the website you're tracking in Matomo."),
    )
    siteimprove_id = models.CharField(
        _("SiteImprove ID"),
        max_length=10,
        default="",
        blank=True,
        help_text=_(
            "SiteImprove ID - this can be found in the snippet example, "
            "which should contain a URL like '//siteimproveanalytics.com/js/siteanalyze_xxxxx.js'. "
            "The xxxxx part is the ID."
        ),
    )
    cookie_info_text = models.CharField(
        max_length=255,
        default=_(
            "Wij gebruiken cookies om onze website en dienstverlening te verbeteren."
        ),
        blank=True,
        verbose_name=_("Cookie info text"),
        help_text=_(
            "The text that displays inside the cookie banner. Supplying this makes the cookie banner visible."
        ),
    )
    cookie_link_text = models.CharField(
        max_length=255,
        default=_("Lees meer over ons cookiebeleid."),
        blank=True,
        verbose_name=_("Cookie link text"),
        help_text=_("The text that is displayed as the link to the cookie policy."),
    )
    cookie_link_url = models.CharField(
        max_length=255,
        default="/pages/privacyverklaring/",
        blank=True,
        verbose_name=_("Privacy page link"),
        help_text=_("The link to the cookie policy page."),
    )
    openid_connect_logo = FilerImageField(
        verbose_name=_("Openid Connect Logo"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="oidc_logo",
        help_text=_("Logo that can be used for the OpenId connect login method"),
    )
    openid_connect_login_text = models.CharField(
        verbose_name=_("Openid Connect login text"),
        max_length=250,
        default="Login with Azure AD",
        help_text=_(
            "The text that should display when OpenId connect is set as a login method"
        ),
    )
    openid_display = models.CharField(
        verbose_name=_("Show option to login via OpenId"),
        max_length=24,
        choices=OpenIDDisplayChoices.choices,
        default=OpenIDDisplayChoices.admin,
        validators=[validate_oidc_config],
        help_text=_("Only selected groups will see the option to login via OpenId."),
    )
    redirect_to = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Redirect anonymous user to"),
        help_text=_(
            "Provide a url or a path where the user should be redirected to from the anonymous page. "
            "Path example: '/accounts/login/', "
            "Url example: 'https://www.example.com'"
        ),
    )
    allow_messages_file_sharing = models.BooleanField(
        verbose_name=_("Allow messages file sharing"),
        default=True,
        help_text=_("Whether file sharing via the messages is allowed or not"),
    )
    hide_categories_from_anonymous_users = models.BooleanField(
        verbose_name=_("Hide categories from anonymous users"),
        default=False,
        help_text=_(
            "If checked, categories will be hidden from users who are not logged in."
        ),
    )
    hide_search_from_anonymous_users = models.BooleanField(
        verbose_name=_("Hide search from anonymous users"),
        default=False,
        help_text=_(
            "If checked, only authenticated users will be able to search the page."
        ),
    )
    display_social = models.BooleanField(
        verbose_name=_("Display social media buttons"),
        default=True,
        help_text=_(
            "Enable sharing of products on social media (Facebook, LinkedIn...)",
        ),
    )
    theme_stylesheet = models.FileField(
        upload_to="themes/",
        verbose_name=_("Theme stylesheet"),
        help_text=_("Additional CSS file added to the page."),
        validators=[FileExtensionValidator(["css"])],
        blank=True,
        null=True,
    )
    extra_css = CSSField(
        blank=True,
        verbose_name=_("Extra CSS"),
        help_text=_(
            "Additional CSS added to the page. Note only a (safe) subset of CSS properties is supported."
        ),
    )
    # authentication options
    eherkenning_enabled = models.BooleanField(
        verbose_name=_("eHerkenning authentication enabled"),
        default=False,
        help_text=_(
            "Whether users can log in with eHerkenning or not. "
            "By default, the SAML integration will be used for this, in order to use "
            "the OpenID Connect integration, navigate to `OpenID Connect configuration for eHerkenning` and enable it."
        ),
    )

    class Meta:
        verbose_name = _("Site Configuration")

    def __str__(self):
        return str(_("Site Configuration"))

    def save(self, *args, **kwargs):
        if self.extra_css:
            self.extra_css = clean_stylesheet(self.extra_css)
        super().save(*args, **kwargs)

    @property
    def get_primary_color(self):
        return hex_to_hsl(self.primary_color)

    @property
    def get_secondary_color(self):
        return hex_to_hsl(self.secondary_color)

    @property
    def get_accent_color(self):
        return hex_to_hsl(self.accent_color)

    @property
    def get_ordered_flatpages(self):
        return self.flatpages.order_by("ordered_flatpages")

    @property
    def google_enabled(self):
        return self.gtm_code and self.ga_code

    @property
    def matomo_enabled(self):
        return self.matomo_url and self.matomo_site_id

    @property
    def siteimprove_enabled(self):
        return bool(self.siteimprove_id)

    @property
    def cookiebanner_enabled(self):
        return bool(self.cookie_info_text)

    @property
    def openid_enabled_for_admin(self):
        return self.openid_display == OpenIDDisplayChoices.admin

    @property
    def openid_enabled_for_regular_users(self):
        return self.openid_display == OpenIDDisplayChoices.regular

    def get_help_text(self, request) -> Optional[str]:
        match = request.resolver_match
        path = request.get_full_path()
        if not match:
            return ""

        lookup = {
            "pages-root": "home_help_text",
            "products:category_list": "theme_help_text",
            "products:category_product_detail": "product_help_text",
            "products:product_detail": "product_help_text",
            "products:product_form": "product_help_text",
            "search:search": "search_help_text",
            "profile:detail": "account_help_text",
            "products:questionnaire_list": "questionnaire_help_text",
            "collaborate:plan_list": "plan_help_text",
            "pages-cookieroot": "cookie_info_text",
            "pages-cookie": "cookie_link_text",
        }

        attr = lookup.get(match.view_name, "")
        if attr:
            return getattr(self, attr)
        elif path in ("", "/"):
            return self.home_help_text
        else:
            return ""


class CustomFontField(models.FileField):
    def __init__(self, file_name: str = "", **kwargs):
        self.file_name = file_name
        super().__init__(**kwargs)


class CustomFontSet(models.Model):
    def update_filename(self, filename: str, new_name: str, path: str) -> str:
        ext = filename.split(".")[1]
        filename = f"{new_name}.{ext}"
        return "{path}/{filename}".format(path=path, filename=filename)

    def update_filename_body(self, filename: str) -> str:
        return CustomFontSet.update_filename(
            self,
            filename,
            new_name=CustomFontName.body,
            path="custom_fonts/",
        )

    def update_filename_body_italic(self, filename: str) -> str:
        return CustomFontSet.update_filename(
            self,
            filename,
            new_name=CustomFontName.body_italic,
            path="custom_fonts/",
        )

    def update_filename_body_bold(self, filename: str) -> str:
        return CustomFontSet.update_filename(
            self,
            filename,
            new_name=CustomFontName.body_bold,
            path="custom_fonts/",
        )

    def update_filename_body_bold_italic(self, filename: str) -> str:
        return CustomFontSet.update_filename(
            self,
            filename,
            new_name=CustomFontName.body_bold_italic,
            path="custom_fonts/",
        )

    def update_filename_heading(self, filename: str) -> str:
        return CustomFontSet.update_filename(
            self,
            filename,
            new_name=CustomFontName.heading,
            path="custom_fonts/",
        )

    heading_font = CustomFontField(
        verbose_name=_("Heading font"),
        upload_to=update_filename_heading,
        file_name=CustomFontName.heading,
        storage=OverwriteStorage(),
        validators=[FileExtensionValidator(["ttf"])],
        blank=True,
        null=True,
        help_text=_("Upload heading font. TTF font types only."),
    )
    site_configuration = models.OneToOneField(
        SiteConfiguration,
        verbose_name=_("Configuration"),
        related_name="custom_fonts",
        on_delete=models.CASCADE,
    )
    body_font_regular = CustomFontField(
        verbose_name=_("Body font regular"),
        upload_to=update_filename_body,
        file_name=CustomFontName.body,
        storage=OverwriteStorage(),
        validators=[FileExtensionValidator(["ttf"])],
        blank=True,
        null=True,
        help_text=_("Upload regular text body font. TTF font types only."),
    )
    body_font_italic = CustomFontField(
        verbose_name=_("Body font italic"),
        upload_to=update_filename_body_italic,
        file_name=CustomFontName.body_italic,
        storage=OverwriteStorage(),
        validators=[FileExtensionValidator(["ttf"])],
        blank=True,
        null=True,
        help_text=_("Upload italic text body font. TTF font types only."),
    )
    body_font_bold = CustomFontField(
        verbose_name=_("Body font bold"),
        upload_to=update_filename_body_bold,
        file_name=CustomFontName.body_bold,
        storage=OverwriteStorage(),
        validators=[FileExtensionValidator(["ttf"])],
        blank=True,
        null=True,
        help_text=_("Upload bold text body font. TTF font types only."),
    )
    body_font_bold_italic = CustomFontField(
        verbose_name=_("Body font bold italic"),
        upload_to=update_filename_body_bold_italic,
        file_name=CustomFontName.body_bold_italic,
        storage=OverwriteStorage(),
        validators=[FileExtensionValidator(["ttf"])],
        blank=True,
        null=True,
        help_text=_("Upload bold italic text body font. TTF font types only."),
    )


@receiver(post_save, sender=CustomFontSet)
def remove_orphan_files(sender, instance, *args, **kwargs):
    """
    Remove font files corresponding to `CustomFont` fields that have been cleared
    """
    custom_fonts_dir = os.path.join(settings.MEDIA_ROOT, "custom_fonts")
    font_names = os.listdir(custom_fonts_dir)

    for field in sender._meta.concrete_fields:
        if isinstance(field, models.FileField) and not getattr(instance, field.name):
            for font_name in font_names:
                if font_name.startswith(field.file_name):
                    os.remove(os.path.join(custom_fonts_dir, font_name))


class SiteConfigurationPage(OrderedModel):
    configuration = models.ForeignKey(
        SiteConfiguration,
        verbose_name=_("Configuration"),
        related_name="ordered_configurations",
        on_delete=models.CASCADE,
    )
    flatpage = models.ForeignKey(
        FlatPage,
        verbose_name=_("Flatpage"),
        related_name="ordered_flatpages",
        on_delete=models.CASCADE,
    )
    order_with_respect_to = "configuration"

    objects = OrderedModelManager()

    class Meta:
        verbose_name = _("Flatpage in the footer")
        verbose_name_plural = _("Flatpages in the footer")

    def __str__(self):
        return self.flatpage.title
