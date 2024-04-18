.. _siteconfig:


=====================
General configuration
=====================


Settings Overview
=================

Required:
"""""""""

::

    SITE_ACCENT_COLOR
    SITE_NAME
    SITE_PRIMARY_COLOR
    SITE_SECONDARY_COLOR
    


All settings:
"""""""""""""

::

    SITE_ACCENT_COLOR
    SITE_ACCENT_FONT_COLOR
    SITE_ACCOUNT_HELP_TEXT
    SITE_ALLOW_MESSAGES_FILE_SHARING
    SITE_CONTACT_PAGE
    SITE_CONTACT_PHONENUMBER
    SITE_COOKIE_INFO_TEXT
    SITE_COOKIE_LINK_TEXT
    SITE_COOKIE_LINK_URL
    SITE_DISPLAY_SOCIAL
    SITE_EHERKENNING_ENABLED
    SITE_EMAIL_NEW_MESSAGE
    SITE_EMAIL_VERIFICATION_REQUIRED
    SITE_FOOTER_LOGO_TITLE
    SITE_FOOTER_LOGO_URL
    SITE_GA_CODE
    SITE_GTM_CODE
    SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS
    SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS
    SITE_HOME_HELP_TEXT
    SITE_HOME_MAP_INTRO
    SITE_HOME_MAP_TITLE
    SITE_HOME_PRODUCT_FINDER_INTRO
    SITE_HOME_PRODUCT_FINDER_TITLE
    SITE_HOME_QUESTIONNAIRE_INTRO
    SITE_HOME_QUESTIONNAIRE_TITLE
    SITE_HOME_THEME_INTRO
    SITE_HOME_THEME_TITLE
    SITE_HOME_WELCOME_INTRO
    SITE_HOME_WELCOME_TITLE
    SITE_KCM_SURVEY_LINK_TEXT
    SITE_KCM_SURVEY_LINK_URL
    SITE_LOGIN_2FA_SMS
    SITE_LOGIN_ALLOW_REGISTRATION
    SITE_LOGIN_SHOW
    SITE_LOGIN_TEXT
    SITE_MATOMO_SITE_ID
    SITE_MATOMO_URL
    SITE_NAME
    SITE_OPENID_CONNECT_LOGIN_TEXT
    SITE_OPENID_DISPLAY
    SITE_PLANS_EDIT_MESSAGE
    SITE_PLANS_INTRO
    SITE_PLANS_NO_PLANS_MESSAGE
    SITE_PLAN_HELP_TEXT
    SITE_PRIMARY_COLOR
    SITE_PRIMARY_FONT_COLOR
    SITE_PRODUCT_HELP_TEXT
    SITE_QUESTIONNAIRE_HELP_TEXT
    SITE_RECIPIENTS_EMAIL_DIGEST
    SITE_REDIRECT_TO
    SITE_REGISTRATION_TEXT
    SITE_SEARCH_FILTER_CATEGORIES
    SITE_SEARCH_FILTER_ORGANIZATIONS
    SITE_SEARCH_FILTER_TAGS
    SITE_SEARCH_HELP_TEXT
    SITE_SECONDARY_COLOR
    SITE_SECONDARY_FONT_COLOR
    SITE_SELECT_QUESTIONNAIRE_INTRO
    SITE_SELECT_QUESTIONNAIRE_TITLE
    SITE_SITEIMPROVE_ID
    SITE_THEME_HELP_TEXT
    SITE_THEME_INTRO
    SITE_THEME_TITLE
    SITE_WARNING_BANNER_BACKGROUND_COLOR
    SITE_WARNING_BANNER_ENABLED
    SITE_WARNING_BANNER_FONT_COLOR
    SITE_WARNING_BANNER_TEXT
    


Detailed Information
====================

::

    Variable            SITE_NAME
    Setting             Naam
    Description         Naam van de gemeente
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_PRIMARY_COLOR
    Setting             Primaire kleur
    Description         Hoofdkleur van de gemeentesite/huisstijl
    Model field type    CharField
    Possible values     string
    Default value       #FFFFFF
    
    Variable            SITE_SECONDARY_COLOR
    Setting             Secundaire kleur
    Description         Secundaire kleur van de gemeentesite/huisstijl
    Model field type    CharField
    Possible values     string
    Default value       #FFFFFF
    
    Variable            SITE_ACCENT_COLOR
    Setting             Accentkleur
    Description         Accentkleur van de gemeentesite/huisstijl
    Model field type    CharField
    Possible values     string
    Default value       #FFFFFF
    
    Variable            SITE_PRIMARY_FONT_COLOR
    Setting             Primaire tekstkleur
    Description         De tekstkleur voor wanneer de achtergrond de hoofdkleur is
    Model field type    CharField
    Possible values     string
    Default value       #FFFFFF
    
    Variable            SITE_SECONDARY_FONT_COLOR
    Setting             Secundaire tekstkleur
    Description         De tekstkleur voor wanneer de achtergrond de secundaire kleur is
    Model field type    CharField
    Possible values     string
    Default value       #FFFFFF
    
    Variable            SITE_ACCENT_FONT_COLOR
    Setting             Accent tekstkleur
    Description         De tekstkleur voor wanneer de achtergrond de accentkleur is
    Model field type    CharField
    Possible values     string
    Default value       #4B4B4B
    
    Variable            SITE_WARNING_BANNER_ENABLED
    Setting             Toon waarschuwingsbanner
    Description         Of de waarschuwingsbanner zichtbaar moet zijn of niet.
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            SITE_WARNING_BANNER_TEXT
    Setting             Tekstinhoud waarschuwingsbanner
    Description         De tekst die zichtbaar is in de waarschuwingsbanner
    Model field type    TextField
    Possible values     string
    Default value       No default
    
    Variable            SITE_WARNING_BANNER_BACKGROUND_COLOR
    Setting             Waarschuwingsbanner achtergrond
    Description         Waarschuwingsbanner achtergrondkleur
    Model field type    CharField
    Possible values     string
    Default value       #FFDBAD
    
    Variable            SITE_WARNING_BANNER_FONT_COLOR
    Setting             Waarschuwingsbanner tekst
    Description         De tekstkleur voor de waarschuwingsbanner
    Model field type    CharField
    Possible values     string
    Default value       #000000
    
    Variable            SITE_LOGIN_SHOW
    Setting             Toon inlogknop rechts bovenin
    Description         Wanneer deze optie uit staat dan kan nog wel worden ingelogd via /accounts/login/ , echter het inloggen is verborgen
    Model field type    BooleanField
    Possible values     True, False
    Default value       True
    
    Variable            SITE_LOGIN_ALLOW_REGISTRATION
    Setting             Sta lokale registratie toe
    Description         Wanneer deze optie uit staat is het enkel toegestaan om met DigiD in te loggen. Zet deze instelling aan om ook het inloggen met gebruikersnaam/wachtwoord en het aanmelden zonder DigiD toe te staan.
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            SITE_LOGIN_2FA_SMS
    Setting             Log in met 2FA-met-SMS
    Description         Bepaalt of gebruikers die met gebruikersnaam+wachtwoord inloggen verplicht een SMS verificatiecode dienen in te vullen
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            SITE_LOGIN_TEXT
    Setting             Login tekst
    Description         Deze tekst wordt getoond op de login pagina.
    Model field type    TextField
    Possible values     string
    Default value       No default
    
    Variable            SITE_REGISTRATION_TEXT
    Setting             Registratie tekst
    Description         Deze tekst wordt getoond op de registratie pagina.
    Model field type    TextField
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_WELCOME_TITLE
    Setting             Koptekst homepage
    Description         Koptekst op de homepage
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_HOME_WELCOME_INTRO
    Setting             Introductietekst homepage
    Description         Introductietekst op de homepage
    Model field type    TextField
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_THEME_TITLE
    Setting             Titel 'Onderwerpen' op de homepage  
    Description         Koptekst van de Onderwerpen op de homepage
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_HOME_THEME_INTRO
    Setting             Onderwerpen introductietekst op de homepage
    Description         Introductietekst 'Onderwerpen' op de homepage
    Model field type    TextField
    Possible values     string
    Default value       No default
    
    Variable            SITE_THEME_TITLE
    Setting             Onderwerpen titel
    Description         Titel op de Onderwerpenpagina
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_THEME_INTRO
    Setting             Onderwerpen introductie
    Description         Introductietekst op de onderwerpenpagina
    Model field type    TextField
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_MAP_TITLE
    Setting             Koptekst van de kaart op de homepage
    Description         Koptekst van de kaart op de homepage
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_HOME_MAP_INTRO
    Setting             Introductietekst kaart
    Description         Introductietekst van de kaart op de homepage
    Model field type    TextField
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_QUESTIONNAIRE_TITLE
    Setting             Titel vragenlijst homepage
    Description         Vragenlijst titel op de homepage.
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_HOME_QUESTIONNAIRE_INTRO
    Setting             Introductietekst vragenlijst homepage
    Description         Vragenlijst introductietekst op de homepage.
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_HOME_PRODUCT_FINDER_TITLE
    Setting             Productzoeker titel
    Description         Titel van de productzoeker op de homepage.
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_HOME_PRODUCT_FINDER_INTRO
    Setting             Introductietekst productzoeker homepage
    Description         Introductietekst van de productzoeker op de homepage.
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_SELECT_QUESTIONNAIRE_TITLE
    Setting             Titel vragenlijst widget
    Description         Vragenlijst keuzetitel op de onderwerpen en profielpagina's.
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_SELECT_QUESTIONNAIRE_INTRO
    Setting             Introductietekst vragenlijst widget
    Description         Vragenlijst introductietekst op de onderwerpen en profielpagina's.
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_PLANS_INTRO
    Setting             Introductietekst Samenwerken
    Description         Subtitel voor de planpagina.
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_PLANS_NO_PLANS_MESSAGE
    Setting             Standaardtekst geen samenwerkingen
    Description         Het bericht als een gebruiker nog geen plannen heeft.
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_PLANS_EDIT_MESSAGE
    Setting             Standaardtekst 'doel wijzigen'
    Description         Het bericht wanneer een gebruiker een doel wijzigt.
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_FOOTER_LOGO_TITLE
    Setting             Footer logo title
    Description         The title - help text of the footer logo.
    Model field type    CharField
    Possible values     string
    Default value       
    
    Variable            SITE_FOOTER_LOGO_URL
    Setting             Footer logo link
    Description         The external link for the footer logo.
    Model field type    CharField
    Possible values     string
    Default value       
    
    Variable            SITE_HOME_HELP_TEXT
    Setting             Helptekst homepage
    Description         Helptekst in de popup op de voorpagina
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_THEME_HELP_TEXT
    Setting             Onderwerpen help
    Description         Helptekst in de popup op de onderwerpenpagina
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_PRODUCT_HELP_TEXT
    Setting             Helptekst producten
    Description         Helptekst in de popup van de productenpagina's
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_SEARCH_HELP_TEXT
    Setting             Helptekst zoeken
    Description         De helptekst in de popup op de zoekpagina's
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_ACCOUNT_HELP_TEXT
    Setting             Helptekst mijn profiel
    Description         De helptekst in de popup van de profielpagina's
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_QUESTIONNAIRE_HELP_TEXT
    Setting             Helptekst vragenlijst/zelftest
    Description         De helptekst in de popup op de vragenlijst/zelftestpagina's
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_PLAN_HELP_TEXT
    Setting             Helptekst samenwerken
    Description         De helptekst in de popup van de samenwerken-pagina's
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            SITE_SEARCH_FILTER_CATEGORIES
    Setting             Onderwerpenfilter toevoegen aan zoekresultaten
    Description         Of er categorie-selectievakjes moeten worden weergegeven om het zoekresultaat te filteren.
    Model field type    BooleanField
    Possible values     True, False
    Default value       True
    
    Variable            SITE_SEARCH_FILTER_TAGS
    Setting             Tagfilter toevoegen aan zoekresultaten
    Description         Of er tag-selectievakjes moeten worden weergegeven om het zoekresultaat te filteren.
    Model field type    BooleanField
    Possible values     True, False
    Default value       True
    
    Variable            SITE_SEARCH_FILTER_ORGANIZATIONS
    Setting             Organisaties-filter toevoegen aan zoekresultaten
    Description         Of er organisatie-selectievakjes moeten worden weergegeven om het zoekresultaat te filteren.
    Model field type    BooleanField
    Possible values     True, False
    Default value       True
    
    Variable            SITE_EMAIL_NEW_MESSAGE
    Setting             Stuur een mail bij nieuwe berichten
    Description         Of er een e-mail ter notificatie verstuurd dient te worden na een nieuw bericht voor de gebruiker.
    Model field type    BooleanField
    Possible values     True, False
    Default value       True
    
    Variable            SITE_RECIPIENTS_EMAIL_DIGEST
    Setting             ontvangers e-mailsamenvatting
    Description         De e-mailadressen van beheerders die een dagelijkse samenvatting dienen te krijgen van punten van orde.
    Model field type    ArrayField
    Possible values     string, comma-delimited ('foo,bar,baz')
    Default value       No information
    
    Variable            SITE_EMAIL_VERIFICATION_REQUIRED
    Setting             Email verification required
    Description         Whether to require users to verify their email address
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            SITE_CONTACT_PHONENUMBER
    Setting             Telefoonnummer
    Description         Telefoonnummer van de organisatie
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_CONTACT_PAGE
    Setting             URL
    Description         URL van de contactpagina van de organisatie
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_GTM_CODE
    Setting             Google Tag Manager code
    Description         Normaalgesproken is dit een code van het formaat 'GTM-XXXX'. Door dit in te stellen wordt Google Tag Manager gebruikt.
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_GA_CODE
    Setting             Google Analytics code
    Description         Normaalgesproken is dit een code van het formaat 'G-XXXX'. Door dit in te stellen wordt Google Analytics gebruikt.
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_MATOMO_URL
    Setting             Matamo server URL
    Description         De domeinnaam / URL van de Matamo server, bijvoorbeeld 'matamo.example.com'.
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_MATOMO_SITE_ID
    Setting             Matamo site ID
    Description         De 'idsite' van de website in Matamo die getrackt dient te worden.
    Model field type    PositiveIntegerField
    Possible values     string representing a (positive) number
    Default value       No default
    
    Variable            SITE_SITEIMPROVE_ID
    Setting             SiteImprove ID
    Description         SiteImprove ID - Dit nummer kan gevonden worden in de SiteImprove snippet, dit is onderdeel van een URL  zoals '//siteimproveanalytics.com/js/siteanalyze_xxxxx.js' waarbij het xxxxx-deel de SiteImprove ID is die hier ingevuld moet worden.
    Model field type    CharField
    Possible values     string
    Default value       
    
    Variable            SITE_COOKIE_INFO_TEXT
    Setting             Tekst cookiebanner informatie
    Description         De tekstinhoud van de cookiebanner. Wanneer deze wordt ingevuld dan wordt de cookiebanner zichtbaar.
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_COOKIE_LINK_TEXT
    Setting             Tekst cookiebanner link
    Description         De tekst die wordt gebruikt als link naar de privacypagina.
    Model field type    CharField
    Possible values     string
    Default value       No information
    
    Variable            SITE_COOKIE_LINK_URL
    Setting             URL van de privacypagina
    Description         De link naar de pagina met het privacybeleid.
    Model field type    CharField
    Possible values     string
    Default value       /pages/privacyverklaring/
    
    Variable            SITE_KCM_SURVEY_LINK_TEXT
    Setting             KCM survey link text
    Description         The text that is displayed on the customer satisfaction survey link
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_KCM_SURVEY_LINK_URL
    Setting             KCM survey URL
    Description         The external link for the customer satisfaction survey.
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_OPENID_CONNECT_LOGIN_TEXT
    Setting             OpenID Connect login tekst
    Description         De tekst die getoond wordt wanneer OpenID Connect (OIDC/Azure AD) als loginmethode is ingesteld
    Model field type    CharField
    Possible values     string
    Default value       Login with Azure AD
    
    Variable            SITE_OPENID_DISPLAY
    Setting             Toon optie om in te loggen via OpenID Connect
    Description         Alleen geselecteerde groepen zullen de optie zien om met OpenID Connect in te loggen.
    Model field type    CharField
    Possible values     string
    Default value       admin
    
    Variable            SITE_REDIRECT_TO
    Setting             Stuur niet-ingelogde gebruiker door naar
    Description         Geef een URL of pad op waar de niet-ingelogde gebruiker naar toe doorgestuurd moet worden vanuit de niet-ingelogde homepage.Pad voorbeeld: '/accounts/login', URL voorbeeld: 'https://gemeente.groningen.nl'
    Model field type    CharField
    Possible values     string
    Default value       No default
    
    Variable            SITE_ALLOW_MESSAGES_FILE_SHARING
    Setting             Sta het delen van bestanden via Mijn Berichten toe
    Description         Of het delen van bestanden via Mijn Berichten mogelijk is of niet. Indien uitgeschakeld dan kunnen alleen tekstberichten worden verzonden
    Model field type    BooleanField
    Possible values     True, False
    Default value       True
    
    Variable            SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS
    Setting             Blokkeer toegang tot Onderwerpen voor niet-ingelogde gebruikers
    Description         Indien geselecteerd: alleen ingelogde gebruikers hebben toegang tot Onderwerpen.
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS
    Setting             Verberg zoekbalk voor anonieme gebruiker
    Description         Indien geselecteerd: alleen ingelogde gebruikers zien de zoekfunctie.
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            SITE_DISPLAY_SOCIAL
    Setting             Toon sociale media knoppen bij elk product
    Description         Maak het delen mogelijk van producten op sociale media (Facebook, LinkedIn...)
    Model field type    BooleanField
    Possible values     True, False
    Default value       True
    
    Variable            SITE_EHERKENNING_ENABLED
    Setting             eHerkenning authentication ingeschakeld
    Description         Of gebruikers in kunnen loggen met eHerkenning of niet. Standaard wordt de SAML integratie hiervoor gebruikt (van toepassing bij een rechtstreekse aansluiting op een eHerkenning makelaar). Voor het gebruiken van een OpenID Connect (OIDC) koppeling, navigeer naar `OpenID Connect configuratie voor eHerkenning` om deze te activeren.
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    