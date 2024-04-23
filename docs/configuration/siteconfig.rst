.. _siteconfig:

=====================
General Configuration
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

    Variable            SITE_LOGIN_2FA_SMS
    Setting             Log in met 2FA-met-SMS
    Description         Bepaalt of gebruikers die met gebruikersnaam+wachtwoord inloggen verplicht een SMS verificatiecode dienen in te vullen
    Possible values     True, False
    Default value       No default
    
    Variable            SITE_KCM_SURVEY_LINK_URL
    Setting             Feedbackknop URL
    Description         De externe link achter de feedbackknop feedback.
    Possible values     string
    Default value       No default
    
    Variable            SITE_HIDE_SEARCH_FROM_ANONYMOUS_USERS
    Setting             Verberg zoekbalk voor anonieme gebruiker
    Description         Indien geselecteerd: alleen ingelogde gebruikers zien de zoekfunctie.
    Possible values     True, False
    Default value       No default
    
    Variable            SITE_QUESTIONNAIRE_HELP_TEXT
    Setting             Helptekst vragenlijst/zelftest
    Description         De helptekst in de popup op de vragenlijst/zelftestpagina's
    Possible values     string
    Default value       Het onderdeel Zelftest stelt u in staat om met het beantwoorden van enkele vragen een advies te krijgen van de gemeente, met concrete vervolgstappen en producten en diensten. U kunt tevens uw antwoorden en het advies bewaren om met een begeleider van de gemeente te bespreken.
    
    Variable            SITE_SECONDARY_FONT_COLOR
    Setting             Secundaire tekstkleur
    Description         De tekstkleur voor wanneer de achtergrond de secundaire kleur is
    Possible values     #FFFFFF, #4B4B4B
    Default value       #FFFFFF
    
    Variable            SITE_PRIMARY_COLOR
    Setting             Primaire kleur
    Description         Hoofdkleur van de gemeentesite/huisstijl
    Possible values     string
    Default value       #FFFFFF
    
    Variable            SITE_ACCENT_COLOR
    Setting             Accentkleur
    Description         Accentkleur van de gemeentesite/huisstijl
    Possible values     string
    Default value       #FFFFFF
    
    Variable            SITE_KCM_SURVEY_LINK_TEXT
    Setting             Feedbackknop label
    Description         De label van de knop wat wordt gebruikt om gebruikersfeedback te verzamelen
    Possible values     string
    Default value       No default
    
    Variable            SITE_SELECT_QUESTIONNAIRE_INTRO
    Setting             Introductietekst vragenlijst widget
    Description         Vragenlijst introductietekst op de onderwerpen en profielpagina's.
    Possible values     string
    Default value       Kies hieronder één van de volgende vragenlijsten om de zelftest te starten.
    
    Variable            SITE_EMAIL_VERIFICATION_REQUIRED
    Setting             E-mailverificatie vereist
    Description         Of gebruikers verplicht zijn om na het inloggen hun e-mailadres te verifieren
    Possible values     True, False
    Default value       No default
    
    Variable            SITE_MATOMO_URL
    Setting             Matamo server URL
    Description         De domeinnaam / URL van de Matamo server, bijvoorbeeld 'matamo.example.com'.
    Possible values     string
    Default value       No default
    
    Variable            SITE_PLANS_INTRO
    Setting             Introductietekst Samenwerken
    Description         Subtitel voor de planpagina.
    Possible values     string
    Default value       Hier werkt u aan uw doelen. Dit doet u samen met uw contactpersoon bij de gemeente. 
    
    Variable            SITE_LOGIN_ALLOW_REGISTRATION
    Setting             Sta lokale registratie toe
    Description         Wanneer deze optie uit staat is het enkel toegestaan om met DigiD in te loggen. Zet deze instelling aan om ook het inloggen met gebruikersnaam/wachtwoord en het aanmelden zonder DigiD toe te staan.
    Possible values     True, False
    Default value       No default
    
    Variable            SITE_NAME
    Setting             Naam
    Description         Naam van de gemeente
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_THEME_TITLE
    Setting             Titel 'Onderwerpen' op de homepage  
    Description         Koptekst van de Onderwerpen op de homepage
    Possible values     string
    Default value       Onderwerpen
    
    Variable            SITE_SELECT_QUESTIONNAIRE_TITLE
    Setting             Titel vragenlijst widget
    Description         Vragenlijst keuzetitel op de onderwerpen en profielpagina's.
    Possible values     string
    Default value       Keuze zelftest?
    
    Variable            SITE_FOOTER_LOGO_TITLE
    Setting             Footer logo title
    Description         The title - help text of the footer logo.
    Possible values     string
    Default value       No default
    
    Variable            SITE_EHERKENNING_ENABLED
    Setting             eHerkenning authentication ingeschakeld
    Description         Of gebruikers in kunnen loggen met eHerkenning of niet. Standaard wordt de SAML integratie hiervoor gebruikt (van toepassing bij een rechtstreekse aansluiting op een eHerkenning makelaar). Voor het gebruiken van een OpenID Connect (OIDC) koppeling, navigeer naar `OpenID Connect configuratie voor eHerkenning` om deze te activeren.
    Possible values     True, False
    Default value       No default
    
    Variable            SITE_THEME_TITLE
    Setting             Onderwerpen titel
    Description         Titel op de Onderwerpenpagina
    Possible values     string
    Default value       Onderwerpen
    
    Variable            SITE_PLAN_HELP_TEXT
    Setting             Helptekst samenwerken
    Description         De helptekst in de popup van de samenwerken-pagina's
    Possible values     string
    Default value       Met het onderdeel Samenwerken kunt u samen met uw contactpersonen of begeleider van de gemeente aan de slag om met een samenwerkingsplan uw persoonlijke situatie te verbeteren. Door samen aan uw doelen te werken en acties te omschrijven kunnen we elkaar helpen.
    
    Variable            SITE_GTM_CODE
    Setting             Google Tag Manager code
    Description         Normaalgesproken is dit een code van het formaat 'GTM-XXXX'. Door dit in te stellen wordt Google Tag Manager gebruikt.
    Possible values     string
    Default value       No default
    
    Variable            SITE_DISPLAY_SOCIAL
    Setting             Toon sociale media knoppen bij elk product
    Description         Maak het delen mogelijk van producten op sociale media (Facebook, LinkedIn...)
    Possible values     True, False
    Default value       True
    
    Variable            SITE_EMAIL_NEW_MESSAGE
    Setting             Stuur een mail bij nieuwe berichten
    Description         Of er een e-mail ter notificatie verstuurd dient te worden na een nieuw bericht voor de gebruiker.
    Possible values     True, False
    Default value       True
    
    Variable            SITE_PLANS_NO_PLANS_MESSAGE
    Setting             Standaardtekst geen samenwerkingen
    Description         Het bericht als een gebruiker nog geen plannen heeft.
    Possible values     string
    Default value       U heeft nog geen plan gemaakt.
    
    Variable            SITE_GA_CODE
    Setting             Google Analytics code
    Description         Normaalgesproken is dit een code van het formaat 'G-XXXX'. Door dit in te stellen wordt Google Analytics gebruikt.
    Possible values     string
    Default value       No default
    
    Variable            SITE_ACCOUNT_HELP_TEXT
    Setting             Helptekst mijn profiel
    Description         De helptekst in de popup van de profielpagina's
    Possible values     string
    Default value       Op dit scherm ziet u uw persoonlijke profielgegevens en gerelateerde gegevens.
    
    Variable            SITE_SITEIMPROVE_ID
    Setting             SiteImprove ID
    Description         SiteImprove ID - Dit nummer kan gevonden worden in de SiteImprove snippet, dit is onderdeel van een URL  zoals '//siteimproveanalytics.com/js/siteanalyze_xxxxx.js' waarbij het xxxxx-deel de SiteImprove ID is die hier ingevuld moet worden.
    Possible values     string
    Default value       No default
    
    Variable            SITE_CONTACT_PAGE
    Setting             URL
    Description         URL van de contactpagina van de organisatie
    Possible values     string
    Default value       No default
    
    Variable            SITE_MATOMO_SITE_ID
    Setting             Matamo site ID
    Description         De 'idsite' van de website in Matamo die getrackt dient te worden.
    Possible values     string representing a positive number
    Default value       No default
    
    Variable            SITE_COOKIE_INFO_TEXT
    Setting             Tekst cookiebanner informatie
    Description         De tekstinhoud van de cookiebanner. Wanneer deze wordt ingevuld dan wordt de cookiebanner zichtbaar.
    Possible values     string
    Default value       Wij gebruiken cookies om onze website en dienstverlening te verbeteren.
    
    Variable            SITE_HOME_QUESTIONNAIRE_INTRO
    Setting             Introductietekst vragenlijst homepage
    Description         Vragenlijst introductietekst op de homepage.
    Possible values     string
    Default value       Test met een paar simpele vragen of u recht heeft op een product
    
    Variable            SITE_HOME_HELP_TEXT
    Setting             Helptekst homepage
    Description         Helptekst in de popup op de voorpagina
    Possible values     string
    Default value       Welkom! Op dit scherm vindt u een overzicht van de verschillende onderwerpen en producten & diensten.
    
    Variable            SITE_PRIMARY_FONT_COLOR
    Setting             Primaire tekstkleur
    Description         De tekstkleur voor wanneer de achtergrond de hoofdkleur is
    Possible values     #FFFFFF, #4B4B4B
    Default value       #FFFFFF
    
    Variable            SITE_HOME_PRODUCT_FINDER_TITLE
    Setting             Productzoeker titel
    Description         Titel van de productzoeker op de homepage.
    Possible values     string
    Default value       Productzoeker
    
    Variable            SITE_CONTACT_PHONENUMBER
    Setting             Telefoonnummer
    Description         Telefoonnummer van de organisatie
    Possible values     string
    Default value       No default
    
    Variable            SITE_ACCENT_FONT_COLOR
    Setting             Accent tekstkleur
    Description         De tekstkleur voor wanneer de achtergrond de accentkleur is
    Possible values     #FFFFFF, #4B4B4B
    Default value       #4B4B4B
    
    Variable            SITE_OPENID_DISPLAY
    Setting             Toon optie om in te loggen via OpenID Connect
    Description         Alleen geselecteerde groepen zullen de optie zien om met OpenID Connect in te loggen.
    Possible values     admin, regular
    Default value       admin
    
    Variable            SITE_THEME_INTRO
    Setting             Onderwerpen introductie
    Description         Introductietekst op de onderwerpenpagina
    Possible values     string
    Default value       No default
    
    Variable            SITE_COOKIE_LINK_URL
    Setting             URL van de privacypagina
    Description         De link naar de pagina met het privacybeleid.
    Possible values     string
    Default value       /pages/privacyverklaring/
    
    Variable            SITE_REDIRECT_TO
    Setting             Stuur niet-ingelogde gebruiker door naar
    Description         Geef een URL of pad op waar de niet-ingelogde gebruiker naar toe doorgestuurd moet worden vanuit de niet-ingelogde homepage.Pad voorbeeld: '/accounts/login', URL voorbeeld: 'https://gemeente.groningen.nl'
    Possible values     string
    Default value       No default
    
    Variable            SITE_WARNING_BANNER_ENABLED
    Setting             Toon waarschuwingsbanner
    Description         Of de waarschuwingsbanner zichtbaar moet zijn of niet.
    Possible values     True, False
    Default value       No default
    
    Variable            SITE_SEARCH_FILTER_CATEGORIES
    Setting             Onderwerpenfilter toevoegen aan zoekresultaten
    Description         Of er categorie-selectievakjes moeten worden weergegeven om het zoekresultaat te filteren.
    Possible values     True, False
    Default value       True
    
    Variable            SITE_SEARCH_FILTER_TAGS
    Setting             Tagfilter toevoegen aan zoekresultaten
    Description         Of er tag-selectievakjes moeten worden weergegeven om het zoekresultaat te filteren.
    Possible values     True, False
    Default value       True
    
    Variable            SITE_RECIPIENTS_EMAIL_DIGEST
    Setting             ontvangers e-mailsamenvatting
    Description         De e-mailadressen van beheerders die een dagelijkse samenvatting dienen te krijgen van punten van orde.
    Possible values     string, comma-delimited ('foo,bar,baz')
    Default value       No default
    
    Variable            SITE_LOGIN_TEXT
    Setting             Login tekst
    Description         Deze tekst wordt getoond op de login pagina.
    Possible values     string
    Default value       No default
    
    Variable            SITE_REGISTRATION_TEXT
    Setting             Registratie tekst
    Description         Deze tekst wordt getoond op de registratie pagina.
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_WELCOME_TITLE
    Setting             Koptekst homepage
    Description         Koptekst op de homepage
    Possible values     string
    Default value       Welkom
    
    Variable            SITE_HOME_THEME_INTRO
    Setting             Onderwerpen introductietekst op de homepage
    Description         Introductietekst 'Onderwerpen' op de homepage
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_QUESTIONNAIRE_TITLE
    Setting             Titel vragenlijst homepage
    Description         Vragenlijst titel op de homepage.
    Possible values     string
    Default value       Waar bent u naar op zoek?
    
    Variable            SITE_PLANS_EDIT_MESSAGE
    Setting             Standaardtekst 'doel wijzigen'
    Description         Het bericht wanneer een gebruiker een doel wijzigt.
    Possible values     string
    Default value       Hier kunt u uw doel aanpassen
    
    Variable            SITE_FOOTER_LOGO_URL
    Setting             Footer logo link
    Description         The external link for the footer logo.
    Possible values     string
    Default value       No default
    
    Variable            SITE_THEME_HELP_TEXT
    Setting             Onderwerpen help
    Description         Helptekst in de popup op de onderwerpenpagina
    Possible values     string
    Default value       Op dit scherm vindt u de verschillende onderwerpen waarvoor wij producten en diensten aanbieden.
    
    Variable            SITE_SEARCH_HELP_TEXT
    Setting             Helptekst zoeken
    Description         De helptekst in de popup op de zoekpagina's
    Possible values     string
    Default value       Op dit scherm kunt u zoeken naar de producten en diensten.
    
    Variable            SITE_SECONDARY_COLOR
    Setting             Secundaire kleur
    Description         Secundaire kleur van de gemeentesite/huisstijl
    Possible values     string
    Default value       #FFFFFF
    
    Variable            SITE_HOME_MAP_TITLE
    Setting             Koptekst van de kaart op de homepage
    Description         Koptekst van de kaart op de homepage
    Possible values     string
    Default value       In de buurt
    
    Variable            SITE_SEARCH_FILTER_ORGANIZATIONS
    Setting             Organisaties-filter toevoegen aan zoekresultaten
    Description         Of er organisatie-selectievakjes moeten worden weergegeven om het zoekresultaat te filteren.
    Possible values     True, False
    Default value       True
    
    Variable            SITE_WARNING_BANNER_FONT_COLOR
    Setting             Waarschuwingsbanner tekst
    Description         De tekstkleur voor de waarschuwingsbanner
    Possible values     string
    Default value       #000000
    
    Variable            SITE_OPENID_CONNECT_LOGIN_TEXT
    Setting             OpenID Connect login tekst
    Description         De tekst die getoond wordt wanneer OpenID Connect (OIDC/Azure AD) als loginmethode is ingesteld
    Possible values     string
    Default value       Login with Azure AD
    
    Variable            SITE_WARNING_BANNER_BACKGROUND_COLOR
    Setting             Waarschuwingsbanner achtergrond
    Description         Waarschuwingsbanner achtergrondkleur
    Possible values     string
    Default value       #FFDBAD
    
    Variable            SITE_LOGIN_SHOW
    Setting             Toon inlogknop rechts bovenin
    Description         Wanneer deze optie uit staat dan kan nog wel worden ingelogd via /accounts/login/ , echter het inloggen is verborgen
    Possible values     True, False
    Default value       True
    
    Variable            SITE_HOME_WELCOME_INTRO
    Setting             Introductietekst homepage
    Description         Introductietekst op de homepage
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_MAP_INTRO
    Setting             Introductietekst kaart
    Description         Introductietekst van de kaart op de homepage
    Possible values     string
    Default value       No default
    
    Variable            SITE_HOME_PRODUCT_FINDER_INTRO
    Setting             Introductietekst productzoeker homepage
    Description         Introductietekst van de productzoeker op de homepage.
    Possible values     string
    Default value       Met een paar simpele vragen ziet u welke producten passen bij uw situatie
    
    Variable            SITE_PRODUCT_HELP_TEXT
    Setting             Helptekst producten
    Description         Helptekst in de popup van de productenpagina's
    Possible values     string
    Default value       Op dit scherm kunt u de details vinden over het gekozen product of dienst. Afhankelijk van het product kunt u deze direct aanvragen of meer informatie opvragen.
    
    Variable            SITE_HIDE_CATEGORIES_FROM_ANONYMOUS_USERS
    Setting             Blokkeer toegang tot Onderwerpen voor niet-ingelogde gebruikers
    Description         Indien geselecteerd: alleen ingelogde gebruikers hebben toegang tot Onderwerpen.
    Possible values     True, False
    Default value       No default
    
    Variable            SITE_COOKIE_LINK_TEXT
    Setting             Tekst cookiebanner link
    Description         De tekst die wordt gebruikt als link naar de privacypagina.
    Possible values     string
    Default value       Lees meer over ons cookiebeleid.
    
    Variable            SITE_ALLOW_MESSAGES_FILE_SHARING
    Setting             Sta het delen van bestanden via Mijn Berichten toe
    Description         Of het delen van bestanden via Mijn Berichten mogelijk is of niet. Indien uitgeschakeld dan kunnen alleen tekstberichten worden verzonden
    Possible values     True, False
    Default value       True
    
    Variable            SITE_WARNING_BANNER_TEXT
    Setting             Tekstinhoud waarschuwingsbanner
    Description         De tekst die zichtbaar is in de waarschuwingsbanner
    Possible values     string
    Default value       No default
