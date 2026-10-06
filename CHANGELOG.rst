2.5.0 (2026-11-03)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.5.0`.

Upgrade informatie
------------------

Pre-upgrade aandachtspunten
~~~~~~~~~~~~~~~~~~~~~~~~~~~

* [:gh:`2594`]: De oude, op omgevingsvariabelen gebaseerde
  setup-configuration-stappen zijn verwijderd. Configuratie via
  ``setup_configuration`` verloopt nu uitsluitend via het YAML-formaat.
  Gebruikt uw installatie een of meer van de volgende omgevingsvariabelen,
  zet die configuratie dan vóór de upgrade om naar het YAML-formaat; na de
  upgrade worden ze genegeerd:

  * alle variabelen die beginnen met ``KIC_``, ``ADMIN_OIDC_``,
    ``DIGID_OIDC_``, ``DIGID_SAML_``, ``EHERKENNING_OIDC_``,
    ``EHERKENNING_SAML_`` of ``CMS_``;
  * alle variabelen die beginnen met ``SITE_``, behalve ``SITE_ID``;
  * de volgende ``ZGW_``-variabelen: ``ZGW_CONFIG_ENABLE``,
    ``ZGW_ZAAK_SERVICE_API_ROOT``, ``ZGW_ZAAK_SERVICE_API_CLIENT_ID``,
    ``ZGW_ZAAK_SERVICE_API_SECRET``, ``ZGW_CATALOGI_SERVICE_API_ROOT``,
    ``ZGW_CATALOGI_SERVICE_API_CLIENT_ID``,
    ``ZGW_CATALOGI_SERVICE_API_SECRET``, ``ZGW_DOCUMENTEN_SERVICE_API_ROOT``,
    ``ZGW_DOCUMENTEN_SERVICE_API_CLIENT_ID``,
    ``ZGW_DOCUMENTEN_SERVICE_API_SECRET``, ``ZGW_FORM_SERVICE_API_ROOT``,
    ``ZGW_FORM_SERVICE_API_CLIENT_ID``, ``ZGW_FORM_SERVICE_API_SECRET``,
    ``ZGW_SERVER_CERTIFICATE_LABEL``, ``ZGW_SERVER_CERTIFICATE_TYPE``,
    ``ZGW_ALLOWED_FILE_EXTENSIONS``, ``ZGW_ZAAK_MAX_CONFIDENTIALITY``,
    ``ZGW_DOCUMENT_MAX_CONFIDENTIALITY``,
    ``ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN``,
    ``ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN``,
    ``ZGW_MIJN_AANVRAGEN_TITLE_TEXT``,
    ``ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE`` en
    ``ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN``;
  * ``OIP_ORGANIZATION``, ``ACTION_REQUIRED_DEADLINE_DAYS`` en
    ``SEARCH_ZERO_RESULTS_TEXT``.

  De volgende variabelen met een vergelijkbaar voorvoegsel worden **niet**
  verwijderd en werken ongewijzigd: ``SITE_ID``, ``DIGID_ENABLED``,
  ``DIGID_MOCK``, ``EHERKENNING_MOCK``, ``ZGW_CACHE_WARMUP_TIMEOUT``,
  ``ZGW_CASE_LIST_FETCH_TIMEOUT``, ``ZGW_CASE_LIST_NUM_WORKERS``,
  ``ZGW_LIMIT_NOTIFICATIONS_FREQUENCY`` en ``ZGW_MAX_REQUESTS``.

  Zie de `documentatie over setup-configuration
  <https://docs.openinwoner.nl/en/v2.5.0/configuration/01_setup_config.html>`_
  voor een volledig overzicht van de beschikbare stappen en velden.
* [:gh:`2828`]: De primaire sleutel van ``NotificationRecord`` is omgezet
  naar een UUID. De migratie vult elke bestaande rij afzonderlijk; houd bij
  een grote tabel rekening met een langere migratieduur (eventueel eerst
  opschonen met ``prune_notification_records``). Uitsluitend relevant voor
  installaties die gebruik maken van de ZGW notificatie functionaliteit. De
  gegevens staan in de tabel ``notifications_notificationrecord`` (in de
  beheeromgeving: 'Notificatieberichten'); het aantal rijen controleert u
  met:

  .. code-block:: sql

      SELECT COUNT(*) FROM notifications_notificationrecord;

Post-upgrade aandachtspunten
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Voor technisch beheerders
^^^^^^^^^^^^^^^^^^^^^^^^^

* [:gh:`3124`]: De aangescherpte CSP geldt nu ook voor medewerkers en voor
  pagina's die eerder buiten de CSP vielen. Controleer na de upgrade of
  eigen JavaScript, ingesloten widgets en externe bronnen (bijv. kaarttegels
  of Open Formulieren) nog werken. Ontbrekende bronnen voegt u toe als
  CSP-instelling in de beheeromgeving. Alleen als laatste redmiddel zet u
  tijdelijk ``CSP_REPORT_ONLY`` aan; de CSP wordt dan niet afgedwongen.
* [:gh:`2681`]: De Permissions Policy wordt standaard afgedwongen. Gebruikt
  uw installatie eigen JavaScript of ingesloten iframes die browserfuncties
  nodig hebben (zoals locatie of camera), test dan eerst met de nieuwe
  omgevingsvariabele ``PERMISSIONS_POLICY_REPORT_ONLY``. Het endpoint
  ``/api/reporting-api/`` is zonder authenticatie bereikbaar; we adviseren
  het in de reverse proxy te rate limiten (zie de documentatie). Het
  endpoint is in te stellen of uit te schakelen via de nieuwe
  omgevingsvariabelen ``REPORTING_API_ENABLED``,
  ``REPORTING_API_MAX_REPORTS_PER_REQUEST``,
  ``REPORTING_API_LOGGING_ENABLED``,
  ``REPORTING_API_MAX_LOGGED_VIOLATIONS_PER_REQUEST`` en
  ``REPORTING_API_METRICS_ENABLED``.
* [:gh:`3109`]: De beperking op het toevoegen van contactpersonen gebruikt
  standaard de default cache (Redis); er is geen actie vereist. Alleen als u
  hiervoor een aparte cache wilt gebruiken, dan stelt u die in via de
  nieuwe, optionele omgevingsvariabelen
  ``CACHE_NOTIFICATION_THROTTLE_BACKEND``,
  ``CACHE_NOTIFICATION_THROTTLE_LOCATION``,
  ``CACHE_NOTIFICATION_THROTTLE_CLIENT_CLASS`` en
  ``CACHE_NOTIFICATION_THROTTLE_IGNORE_EXCEPTIONS``.
* [:gh:`2638`]: Celery beat plant nu elke minuut een taak in, zodat de
  health check ``maykin-common beat-health-check`` betrouwbaar aangeeft of
  beat nog taken inplant. We adviseren deze in te stellen als liveness probe
  voor de celery-beat-container, bijvoorbeeld met ``--max-age 1200``.

Voor functioneel beheerders
^^^^^^^^^^^^^^^^^^^^^^^^^^^

* [:gh:`2766`]: Datamigraties schonen links en afbeeldingen op in door
  beheerders ingevoerde opgemaakte tekst (ProseMirror), o.a. in de
  siteconfiguratie, CMS-plugins, de footer, producten, zaaktypen, OpenKlant,
  vragenlijsten en SSD. Links met een ander URL-schema dan ``http``,
  ``https``, ``mailto`` of ``tel`` worden verwijderd (de tekst blijft
  staan); afbeeldingen met zo'n URL worden in hun geheel verwijderd. Elke
  verwijdering wordt tijdens de migratie als waarschuwing gelogd. Controleer
  na de upgrade de gelogde waarschuwingen en de opgemaakte teksten met links,
  en zet waar nodig een correcte link terug.
* [:gh:`2893`]: Het gebruikersmenu toont alleen nog 'Mijn profiel'; alle
  andere onderdelen zijn uitsluitend bereikbaar via de zijnavigatie, die wordt
  opgebouwd uit de CMS-paginaboom. Controleer na de upgrade of alle
  onderdelen die inwoners moeten kunnen bereiken als gepubliceerde pagina in
  de paginaboom staan, zoals de nieuwe 'Mijn vragen'-pagina (zie
  :gh:`2744`).
* [:gh:`3095`]: De lijst van toegestane plugins voor de footer (links, midden
  en rechts) en de loginbanner wordt nu daadwerkelijk toegepast. Voorheen gold
  voor deze statische aliassen een algemene lijst, waardoor bijvoorbeeld de
  plugin 'Pagina lijst' of een losse link niet kon worden toegevoegd, maar
  plugins als 'Zaken' of 'Video' wel. Controleer na de upgrade de inhoud van de
  footer en de loginbanner.
* [:gh:`2830`]: De standaardkleuren van ``SiteConfiguration`` zijn aangepast
  zodat tekst- en achtergrondkleur voldoende contrast hebben. Dit raakt
  alleen installaties die de kleuren nooit zelf hebben ingesteld; controleer
  de huisstijl na de upgrade.
* [:gh:`2969`]: Een datamigratie zet de CMS-pagina van het contactformulier
  om naar het juiste paginasjabloon, zodat het contactformulier weer te
  bewerken is. Controleer na de upgrade het contactformulier.
* [:gh:`2833`]: Een datamigratie zet de aan ``OpenKlant2Config`` gekoppelde
  ``Service`` om naar ``auth_type=api_key`` met
  ``Authorization: Token <secret>`` als header. Controleer na de upgrade of
  de pagina's die gegevens uit OpenKlant tonen nog correct werken, zoals
  'Mijn vragen' en 'Mijn Profiel'.

Uitfaseringen
~~~~~~~~~~~~~

De volgende wijzigingen worden doorgevoerd in de volgende feature release.

* De logging wordt gestandaardiseerd. Alle logs, ook die van
  de webserver, worden als JSON geschreven, en de logbestanden worden
  samengevoegd. Sentry ontvangt alleen nog niet-afgevangen fouten; afgehandelde
  fouten zijn alleen nog in de logs terug te vinden. Houd hier rekening mee
  bij het verwerken van de logs en het inrichten van monitoring.

Belangrijkste verbeteringen
---------------------------

* [:gh:`2894`]: De menustructuur van de beheeromgeving is gewijzigd.
  Onderdelen zijn opnieuw ingedeeld in de hoofdgroepen 'Gebruikers &
  Authenticatie', 'Modules', 'Koppelingen', 'Beheer', 'Logging' en
  'Overige', met gerelateerde onderdelen in subgroepen daaronder.
* [:gh:`2893`]: Voorheen werd de zijnavigatie voor ingelogde gebruikers alleen
  op een deel van de pagina's getoond; nu volgen alle pagina's dit design.
  Het gebruikersmenu toont daardoor alleen nog 'Mijn profiel';
  de overige onderdelen zijn via de zijnavigatie bereikbaar. In het mobiele
  menu is de zoekoptie verwijderd.
* [:gh:`2744`]: Verbeteringen aan 'Mijn vragen' (OpenKlant2):

  * Reacties worden opgehaald ongeacht het kanaal waarlangs ze zijn
    geregistreerd; ``mijn_vragen_kanaal`` geldt nu alleen nog bij het
    aanmaken van vragen, niet meer voor het ophalen.
  * Alle antwoorden op een vraag worden getoond, niet alleen de nieuwste.
  * Een vraag krijgt de status 'Afgehandeld' zodra alle daaraan gekoppelde
    interne taken verwerkt zijn.
  * Reacties die naast de oorspronkelijke vraag ook naar de zaak verwijzen,
    worden op de zaakpagina niet langer als aparte vraag getoond.
  * Als niet alle reacties binnen een gesprek opgehaald kunnen worden, toont
    de lijst 'Mijn vragen' een melding dat het overzicht onvolledig is.
  * 'Mijn vragen' kan een eigen ingang in de zijnavigatie krijgen via een
    nieuwe ``mijn_vragen`` redirect-pagina in de CMS-pagina-configuratie.

* [:gh:`2617`]: Per zaaktypeconfiguratie kan een datum worden ingesteld
  ("Show cases from date"); zaken met een startdatum vóór die datum zijn dan
  niet zichtbaar voor inwoners. Dit geldt overal: in 'Mijn zaken', de
  zoekresultaten en notificaties, en de zaakpagina is ook via een directe
  link niet bereikbaar. Leeg laten behoudt het huidige gedrag.
* [:gh:`2904`]: Betere caching van stylesheets, scripts en afbeeldingen. Deze
  kunnen nu langer door de browser worden bewaard, waardoor pagina's sneller
  laden. Na een upgrade worden gewijzigde bestanden direct opnieuw opgehaald,
  zodat inwoners niet langer een verouderde versie te zien krijgen.

Beveiligingsverbeteringen
-------------------------

* [:gh:`3124`]: De Content Security Policy (CSP) is aangescherpt:

  * De CSP geldt nu ook voor ingelogde medewerkers (staff); voorheen was de
    CSP voor hen op alle pagina's uitgeschakeld. De beheeromgeving blijft
    uitgezonderd.
  * ``default-src`` en ``base-uri`` staan op ``'none'``, alleen de
    API-documentatie (ReDoc) is nog uitgezonderd in plaats van de hele API,
    en ``upgrade-insecure-requests`` is ingeschakeld als de site via HTTPS
    wordt aangeboden.
  * De CSP-instellingen uit de beheeromgeving zijn overgezet naar
    ``maykin-common``; bestaande instellingen, waaronder de PDOK-kaarttegels,
    worden bij de migratie automatisch overgezet. De instellingen staan in
    een eigen groep in het menu van de beheeromgeving.
  * ``CSP_REPORT_PERCENTAGE`` werd voorheen niet toegepast; dat is hersteld.

* [:gh:`2681`]: Open Inwoner stuurt een ``Permissions-Policy``-header mee,
  zodat browserfuncties die de site niet gebruikt (zoals camera, microfoon en
  locatie) ook niet door geïnjecteerde of externe scripts gebruikt kunnen
  worden. Overtredingen worden door browsers gemeld aan het nieuwe endpoint
  ``/api/reporting-api/`` en gelogd en als OpenTelemetry-metriek
  bijgehouden. Zie de `documentatie over de Permissions Policy
  <https://docs.openinwoner.nl/en/v2.5.0/configuration/03_permissions_policy.html>`_.
* [:gh:`3102`]: In de module Samenwerkingen kunnen contactpersonen alleen nog
  worden toegevoegd als ze een account hebben. Er worden geen uitnodigingen
  meer per e-mail verstuurd naar e-mailadressen zonder account; de gebruiker
  krijgt dan een foutmelding met het verzoek de contactpersoon eerst een
  account te laten aanmaken.
* [:gh:`3109`]: Het toevoegen van contactpersonen in de module
  Samenwerkingen is beperkt tot één verzoek per minuut per gebruiker, om
  misbruik voor het versturen van e-mails te voorkomen.
* [:gh:`3169`]: Strengere controle van geüploade bestanden. Het bestandstype
  dat de browser opgeeft kan door een gebruiker worden vervalst, waardoor
  bijvoorbeeld een SVG- of HTML-bestand als afbeelding kon worden geüpload:

  * Bij uploads (o.a. bij berichten, acties en samenwerkingen) moet ook het
    bestandstype dat bij de extensie hoort zijn toegestaan; gecomprimeerde
    bestanden (bv. ``.txt.gz``) worden geweigerd.
  * Bij het uploaden van een document bij een zaak wordt het ``formaat`` in de
    Documenten API afgeleid van de extensie, in plaats van van het opgegeven
    bestandstype.
  * Documenten, bijlagen bij acties en berichten in de inbox worden altijd als
    download aangeboden en niet meer in de browser geopend.
* [:gh:`3101`]: Extra controle op de koppelingen die externe diensten
  teruggeven: Open Inwoner controleert nu zelf of een document bij de zaak
  hoort, zowel op de zaakpagina als bij het downloaden, en of de zaak die op de
  detailpagina van een vraag wordt getoond daadwerkelijk aan die vraag is
  gekoppeld, in plaats van alleen te vertrouwen op de filtering van de API.
  Dit is bedoeld voor backends die niet volledig ZGW-compliant zijn en
  sommige filters negeren; bij volledig compliant backends verandert er niets.

Nieuwe functies
---------------

* [:gh:`3049`]: De beheerdershandleiding is herschreven en volgt nu de
  menustructuur van de beheeromgeving, met een hoofdstuk per onderdeel van het
  menu en per scherm de locatie in het menu. Teksten, veldnamen en knoppen zijn
  gecontroleerd tegen de huidige beheeromgeving en alle schermafbeeldingen zijn
  vernieuwd. Ook de documentatie over configuratie (setup-configuration,
  omgevingsvariabelen) en installatie (Docker Compose, Celery, health checks)
  is bijgewerkt.
* [:gh:`2842`]: Niet-gepubliceerde versies van CMS-pagina's kunnen worden
  verwijderd.
* [:gh:`2897`]: Uitgebreidere keuze aan menu-iconen, met een link naar een
  voorbeeldpagina.
* [:gh:`2886`, :gh:`2922`, :gh:`2987`]: Nieuwe configuratiechecks voor BRP,
  de userfeed en het ophalen van een bedrijf op KvK-nummer. De userfeed-check
  is ook beschikbaar vanuit het gebruikersbeheer. Omdat de checks echte
  verzoeken uitvoeren naar gekoppelde diensten, zijn ze standaard
  uitgeschakeld; zet de nieuwe omgevingsvariabele ``ENABLE_INTERACTIVE_CHECKS``
  op ``True`` om ze in de beheeromgeving te tonen.
* [:gh:`2078`, :gh:`3078`]: Medewerkers (staff) zien alle menu-items, ook van
  pagina's waarvoor inloggen of DigiD/eHerkenning nodig is, en kunnen de
  pagina's 'Mijn zaken' en 'Mijn vragen' openen om ze vanuit de frontend te
  bewerken. Zaken en vragen worden voor hen niet opgehaald.
* [:gh:`1781`]: De helptekst van de knoptekst van een product geeft aan dat
  deze alleen geldt voor knoppen in de inhoud van het product.
* [:gh:`2917`]: Nieuwe setup-configuration-stappen voor SOAP-services en SSD.
  Hiervoor heeft ``SoapService`` een uniek ``slug``-veld gekregen in plaats
  van ``label``; bestaande labels worden bij de migratie automatisch omgezet.
* [:gh:`2827`]: Zaaktypeconfiguraties zijn in het beheerscherm doorzoekbaar
  op onderliggende objecten (statustypen e.d.).
* [:gh:`2801`, :gh:`2807`, :gh:`2853`, :gh:`2855`]: Verbeteringen aan de
  verwerking van ZGW-notificaties (``NotificationRecord``):

  * De uitkomst van de verwerking van een notificatie wordt opgeslagen op het
    ``NotificationRecord``; logging is omgezet naar structlog.
  * De volledige payload van notificaties is doorzoekbaar in de
    beheeromgeving.
  * ``is_valid`` is alleen-lezen in de beheeromgeving.
  * Notificatieberichten worden elk uur opgeschoond in plaats van dagelijks.
    De bewaartermijnen in de notificatie-instellingen worden daarom in uren
    in plaats van dagen ingesteld; bestaande waarden worden automatisch
    omgerekend.
* [:gh:`2638`]: Nieuwe periodieke Celery-taak 'Beat health sentinel' die
  elke minuut draait, zodat de celery-beat health check sneller slaagt. De
  ``start_period`` van de celery-beat healthcheck in Docker Compose is
  verlaagd van 900s naar 120s.
* [:gh:`2679`, :gh:`2696`, :gh:`2755`, :gh:`2956`, :gh:`2990`]:
  Verbeteringen aan Mijn Afval:

  * Een cumulatieve lijn voor kosten en gewicht.
  * Gewichten worden met 2 decimalen getoond.
  * Afvaltypen worden getoond zoals Open Afval ze aanlevert, in plaats van een
    vaste set codes. Het filter op afvaltype biedt de typen die in de gegevens
    voorkomen.
  * Tabelcellen tonen de eenheid bij de waarde (bv. €); numerieke
    waarden worden rechts uitgelijnd.
* [:gh:`2948`]: ``django-upgrade-check`` is geïnstalleerd, zodat de actieve
  versies op installaties worden vastgelegd.
* [:gh:`2873`]: De beheeromgeving gebruikt de standaard huisstijl van
  ``maykin-common``, met licht/donker-thema en omgevingsinformatie. De
  weergave van de omgeving en de branding in de beheeromgeving zijn
  instelbaar via nieuwe, optionele omgevingsvariabelen
  (``ENVIRONMENT_LABEL``, ``ENVIRONMENT_BACKGROUND_COLOR``,
  ``ENVIRONMENT_FOREGROUND_COLOR``, ``SHOW_ENVIRONMENT``,
  ``CUSTOM_PRODUCT_NAME``, ``CUSTOM_PRODUCT_URL``,
  ``CUSTOM_PRODUCT_LOGO_PATH`` en ``CUSTOM_PRODUCT_LOGO_URL``).

Bugfixes
--------

* [:gh:`2831`]: De webserver wordt weer met ``--lazy-apps`` gestart. Het
  weglaten hiervan (2.4.4) leidde opnieuw tot segfaults.
* [:gh:`2804`]: De laadindicator wordt na een timeout verborgen en er wordt
  een foutmelding getoond.
* [:gh:`2915`]: Correcte detectie van het bestandstype bij uploads in
  Samenwerkingen.
* [:gh:`2973`]: De keuzelijst bij het uploaden van documenten toont alleen nog
  de omschrijving van het informatieobjecttype (zonder catalogus-URL).
* [:gh:`2992`]: Broodkruimelpad toegevoegd aan de inbox.
* [:gh:`3008`]: Ontbrekende en onjuiste vertalingen van meldingen bij de
  ZGW-, PDC-, contact- en KvK-import gecorrigeerd.
* [:gh:`2924`, :gh:`2961`]: Diverse uitlijningsproblemen opgelost in Mijn
  Berichten, Mijn Vragen, Mijn Afval, Samenwerken, de detailpagina's en de
  login- en registratiepagina's. Mijn Berichten heeft aangepaste kleuren en
  spacing en een betere weergave op mobiel.
* [:gh:`2797`]: De huidige pagina van de zakenlijst blijft behouden bij het
  herladen.
* [:gh:`2803`]: ``OpenZaakConfig.document_visible_statuses`` mag leeg zijn.
* [:gh:`2885`]: De configuratiecheck ``fetch_cases`` wordt bij het opstarten
  geregistreerd.
* [:gh:`2786`]: De cache van de Laposta-abonnementen wordt op de juiste
  sleutel geïnvalideerd.
* [:gh:`2910`]: Correcte e-mailbackend in ``local_example.py``.
* Logging toegevoegd voor API-fouten bij het uploaden van bestanden.
* [:gh:`3098`]: Toegestane bestandsextensies voor uploads bij zaken die met
  een punt of hoofdletters waren ingesteld (bv. ``.pdf`` of ``PDF``), werden
  nooit herkend, waardoor uploads van dat type werden geweigerd. Bestaande
  waarden worden bij de migratie genormaliseerd (``.PDF`` wordt ``pdf``), en
  extensies die via de beheeromgeving of ``setup_configuration`` worden
  ingesteld, worden op dezelfde manier opgeslagen.
* [:gh:`3059`]: De niet-werkende banner-placeholder van de Samenwerken-pagina
  is verwijderd.
* [:gh:`3077`]: Broodkruimelpaden van CMS-app-pagina's beginnen met de titel
  van de CMS-pagina in plaats van een vaste tekst.
* [:gh:`3092`]: Notificaties die direct door de webhook worden afgerond
  (bijv. bij een ongeldig schema of een niet-geabonneerd kanaal) worden nu
  ook opgeschoond.
* [:gh:`2987`]: De knop voor de configuratiecheck ``fetch_cases`` staat weer
  in de Open Zaak-configuratie in de beheeromgeving.
* [:gh:`2858`]: Verbeterde toetsenbordnavigatie in het filtermenu en de
  keuzevakjes, en het filtermenu werkt weer na een HTMX-update.
* [:gh:`3030`, :gh:`2954`]: Aangepaste opmaak van de zoekpagina en de
  filterknop; de filterknop heet nu 'Filter toepassen'.
* [:gh:`3080`]: Het menu sluit weer als het via het icoon is geopend.
* [:gh:`2936`, :gh:`3026`, :gh:`3043`]: Diverse opmaakproblemen opgelost bij
  het aanmaken van samenwerkingen, de tekst bij een banner en het dashboard op
  mobiel.
* [:gh:`3058`]: Het statusfilter kan weer met de Enter-toets worden
  aan- en uitgevinkt.
* [:gh:`3147`]: De 'Mijn afspraken'-plugin op de homepage en de pagina 'Mijn
  afspraken' tonen geen foutpagina meer als Qmatic niet bereikbaar is of een
  fout teruggeeft.
* [:gh:`2969`]: Nieuwe contactpagina's krijgen het juiste paginasjabloon,
  zodat het contactformulier kan worden toegevoegd en bewerkt.
* [:gh:`3124`]: Een geopend gesprek in de inbox haalt bij het verversen
  alleen nog de berichten op in plaats van de hele pagina, en de datumkiezer
  werkt onder de CSP ook in Safari.
* [:gh:`3129`]: Externe links in CMS-linkplugins, opgemaakte teksten (zoals
  zaakstatussen en producten) en de links bij een product openen standaard in
  een nieuw tabblad.

Onderhoud
---------

* [:gh:`2638`], [:gh:`2917`], [:gh:`2922`], [:gh:`2926`], [:gh:`2931`],
  [:gh:`2932`], [:gh:`2925`], [:gh:`2744`], [:gh:`2994`], [:gh:`2995`],
  [:gh:`2996`], [:gh:`2997`], [:gh:`2998`]: Docker Compose-stack voor lokale
  ontwikkeling uitgebreid met Open Zaak, Objects API's, Haal Centraal
  BRP-mock, OpenKlant, Open Afval, een SSD-mock, KvK, testgebruikers,
  samenwerkingen, openstaande taken, documentuploads en een gevulde
  homepage (banner, producten, categorieën, sitemap). Zie ``bin/stack.sh``.
* [:gh:`2898`]: Ondersteuning voor het lokaal draaien van OIP tegen de
  Docker-stack, inclusief documentatie.
* [:gh:`2933`]: Script om ZGW-notificaties te versturen voor testdoeleinden.
* [:gh:`2924`]: Opschoning van de code van Mijn Berichten.
* [:gh:`2523`]: Nieuwe Open Inwoner-branding in de documentatie.
* [:gh:`2968`]: 'Platform' vervangen door 'Portaal' in de README.
* [:gh:`2662`]: ``COMMIT_HASH`` en ``RELEASE`` worden in het Docker-image
  gezet.
* [:gh:`2947`]: Docker-images zonder arm64-ondersteuning gemarkeerd.
* [:gh:`2785`], [:gh:`2799`]: Refactorings van de formulieren- en
  OpenKlant-clients.
* [:gh:`3038`], [:gh:`3111`], [:gh:`3045`], [:gh:`2956`]: Docker-stack: kaart
  met productlocaties op de homepage, genormaliseerde bestandsextensies,
  Keycloak-sessies worden niet meer hergebruikt tussen logins, en Open Afval
  bijgewerkt naar ``0.11.0``.
* [:gh:`3057`]: Ontbrekende Nederlandse vertalingen aangevuld, o.a. voor de
  nieuwe menu-iconen, configuratiechecks en foutmeldingen, en bestaande
  vertalingen verbeterd, zoals de foutmeldingen bij een ongeldig BSN of
  KvK-nummer.
* Verschillende bibliotheken bijgewerkt, o.a. ``django-treebeard``
  ``5.3.1``, ``django-csp`` ``4.0``, ``opentelemetry-api`` ``1.45.1``,
  ``maykin-common`` ``0.21.0``, ``maykin-django-prosemirror`` ``0.13.0``,
  ``playwright`` ``1.64.0``, ``open-klant-client`` ``0.7.0``,
  ``django-debug-toolbar`` ``8.0.0``, ``werkzeug`` ``3.1.9``, ``sqlparse``,
  ``tablib``, ``webob``, ``soupsieve``, ``dnspython`` ``2.9.1``,
  ``packaging`` ``26.3``, ``virtualenv`` ``21.15.2``, ``distlib``,
  ``filelock``, ``msgpack``, ``design-tokens`` ``0.0.33`` en diverse
  npm-pakketten.
* [:gh:`2681`], [:gh:`2904`]: Nieuwe afhankelijkheden
  ``django-permissions-policy``, ``msgspec`` en ``django-vite``.
* [:gh:`2904`]: In de ontwikkelomgeving worden frontend-bestanden vanaf de
  Vite-devserver geserveerd (``npm run watch``), zodat niet bij elke wijziging
  alle bundles opnieuw gebouwd hoeven te worden. In de Docker Compose-setup
  staat ``DEBUG`` uit.
* [:gh:`3147`], [:gh:`2681`]: Docker-stack: mock-afspraken voor Qmatic en de
  'Mijn afspraken'-plugin op de homepage, en een rate limit op het Reporting
  API-endpoint in de nginx-configuratie.
* CI: Dependabot voor GitHub Actions, controle op het verlopen van de
  KvK-certificaatketen, runners op Ubuntu 26.04 (:gh:`3137`), en diverse
  updates van GitHub Actions.

2.4.9 (2026-10-29)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.9`.

Beveiliging
-----------

* [:gh:`3054`]: De pop-ups van locaties op de kaart binnen de CMS plugin
  "Product Location" worden nu opgebouwd uit DOM-elementen in plaats van uit
  HTML-tekst. Voorheen werden de gegevens van een locatie (zoals de naam) als
  HTML in de pop-up geplaatst, wat ondanks het escapen ruimte liet voor XSS.
  De locatiegegevens konden alleen door beheerders worden toegevoegd, en
  vereiste verder dat de plugin was geactiveerd.

Bugfixes
--------

* [:gh:`3143`]: De PDF-exports van de jaaropgave en de maandspecificatie
  (uitkeringen) waren hun opmaak verloren. De opmaak is hersteld.
* [:gh:`3131`, :gh:`3148`]: De weergave van balie-afspraken in de tegels van
  de 'Mijn afspraken'-plugin op de homepage is verbeterd: de titel toont nu de
  naam van de dienst (zoals 'Paspoort') in plaats van de algemene titel van de
  afspraak, en tussen de tijd en de locatie staat nu een spatie.
* [:gh:`3164`]: Op de CMS pagina 'Mijn afspraken' liep de tekst van de link om een
  afspraak te wijzigen of te annuleren buiten de kaart. De linktekst is
  ingekort tot "Wijzig of annuleer".

Onderhoud
---------

* [:gh:`3017`]: ``PyJWT`` bijgewerkt van ``2.13.0`` naar ``2.15.1``.
* [:gh:`3020`]: ``urllib3`` bijgewerkt van ``2.7.0`` naar ``2.8.0``.
* [:gh:`3063`]: ``geopy`` bijgewerkt van ``2.2.0`` naar ``2.5.0``.

2.4.8 (2026-10-26)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.8`.

.. note::

   Dit is een hotfix-release met beveiligingsupdates voor een aantal
   afhankelijkheden. We adviseren u zo snel mogelijk te upgraden.

Beveiliging
-----------

* [:gh:`3119`]: ``certifi`` is bijgewerkt naar versie ``2026.10.19``. Hiermee
  zijn de gecompromitteerde emSign-rootcertificaten verwijderd uit de lijst met
  vertrouwde certificaten (`GHSA-6q48-6c7w-9gw2
  <https://github.com/advisories/GHSA-6q48-6c7w-9gw2>`_). Het algemene
  aanvalsscenario is een adversary-in-the-middle-aanval, waarbij een aanvaller
  zich voordoet als een externe dienst waarmee Open Inwoner verbinding maakt.
  Een via deze roots uitgegeven certificaat alleen is daarvoor niet voldoende:
  de aanvaller moet ook het netwerkverkeer tussen Open Inwoner en die dienst
  kunnen onderscheppen of omleiden. In een gebruikelijke configuratie schatten
  wij de kans daarop laag in.
* [:gh:`3122`]: ``pillow`` bijgewerkt naar ``13.0.0``.
* ``djangorestframework`` bijgewerkt naar ``3.18.3``.
* [:gh:`3134`]: ``brotli`` bijgewerkt naar ``1.2.1``.
* [:gh:`3025`]: ``Django`` bijgewerkt naar ``5.2.18``.

Deployment aandachtspunten
--------------------------

* [:gh:`3119`]: Na de upgrade worden certificaten die zijn uitgegeven onder een
  emSign-root niet langer vertrouwd. Controleer na de upgrade of de verbindingen
  met externe diensten (zoals ZGW-API's, Haal Centraal, Open Klant en
  e-mail/SMS-providers) nog werken. Mocht een dienst een certificaat gebruiken
  dat onder een emSign-root valt, dan moet de beheerder van die dienst het
  certificaat laten vervangen.

Onderhoud
---------

* [:gh:`3119`]: ``certifi`` bijgewerkt van ``2025.11.12`` naar ``2026.10.19``.

2.4.7 (2026-10-14)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.7`.

.. note::

   Deze release bevat een beveiligingsupdate voor de editor die beheerders en
   redacteuren gebruiken. We adviseren u zo snel mogelijk te upgraden.

Beveiliging
-----------

* ``maykin-django-prosemirror`` is bijgewerkt naar versie ``0.12.0``. Deze
  versie bevat een fix voor de kwetsbaarheid `GHSA-c8x8-7fp4-3x9w
  <https://github.com/advisories/GHSA-c8x8-7fp4-3x9w>`_ (CVE-2026-104847) in
  ``prosemirror-view``: wanneer een gebruiker door een kwaadwillende
  aangeleverde HTML in een ProseMirror-editor plakt, kan JavaScript van die
  kwaadwillende worden uitgevoerd in het browservenster met de editor.

  Alleen beheerders en redacteuren lopen risico: de editor wordt alleen in de
  beheeromgeving en het CMS gebruikt.

Bugfixes
--------

* [:gh:`3059`]: In de structuurweergave van het CMS toonde de keuzelijst voor
  het toevoegen van een plugin alleen de tekstplugin. Bij placeholders die de
  tekstplugin niet toestaan bleef de keuzelijst leeg, bij de overige werd
  direct een tekstplugin toegevoegd. Alle plugins die een placeholder toestaat
  zijn nu weer beschikbaar.
* [:gh:`3075`]: Apphook-pagina's (zoals 'Samenwerken' en 'Mijn profiel')
  konden in de bewerkmodus niet naar de structuurmodus worden geschakeld of
  worden gepubliceerd: de toolbar toonde alleen 'Maken'. Dit is hersteld.
* [:gh:`3088`]: Het aanmaken van een pagina via de wizard van het CMS mislukte
  na het kiezen van het soort pagina met een foutmelding (``TypeError``). Dit
  is hersteld door ``django-formtools`` bij te werken.

Onderhoud
---------

* ``maykin-django-prosemirror`` bijgewerkt naar versie ``0.12.0``.
* [:gh:`3088`]: ``django-formtools`` bijgewerkt van ``2.3`` naar ``2.7``.

2.4.6 (2026-10-06)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.6`.

.. warning::

   Deze release bevat een beveiligingsupdate. Werk zo snel mogelijk bij, en volg
   daarna de stappen onder **Deployment aandachtspunten** om bestaande uploads op
   misbruik te controleren.

Beveiliging
-----------

* ``maykin-django-prosemirror`` is bijgewerkt naar versie ``0.11.0``. Hiermee
  is een kwetsbaarheid in de afbeeldingsendpoints van de editor
  (``/prosemirror/filer-image-upload/``) opgelost. Voorheen kon iedere
  ingelogde gebruiker, dus ook een inwoner of bedrijf ingelogd via DigiD of
  eHerkenning:

  * bestanden van elk type uploaden, waaronder HTML- en SVG-bestanden met
    JavaScript. Deze werden als publieke afbeelding opgeslagen en vanuit
    ``/media/`` geserveerd, wat kon leiden tot stored XSS op het domein van
    Open Inwoner;
  * de metadata van iedere filer-afbeelding opvragen, ook van privé
    afbeeldingen;
  * de naam, beschrijving en het bijschrift van iedere filer-afbeelding
    wijzigen.

  De endpoints zijn nu alleen beschikbaar voor medewerkers (staff) met de
  juiste filer-permissies, en uploads worden gecontroleerd op het bestandstype.
  Alle installaties vanaf versie ``2.0.0`` zijn kwetsbaar, ongeacht de
  configuratie.

Deployment aandachtspunten
--------------------------

* **Controleer na het bijwerken de bestaande afbeeldingen op misbruik.** Voer
  hiervoor het volgende commando uit:

  .. code-block:: bash

      python src/manage.py check_filer_images

  Het commando controleert alle filer-afbeeldingen en geeft elke afbeelding een
  oordeel:

  * ``SUSPICIOUS``: moet bekeken worden. Het bestand is geen afbeelding
    (bijvoorbeeld HTML), het is een SVG met scripts, event handlers of
    ingebedde data, het zou met een ander content type dan een afbeelding
    worden geserveerd, of het wordt om een andere reden door de
    uploadvalidatie geweigerd.
  * ``UNCHECKED``: het bestand bestaat, maar kon niet worden gelezen
    (bijvoorbeeld door een fout in de opslag). Voer het commando later opnieuw
    uit.
  * ``NOTE``: zou nu niet als upload worden geaccepteerd, maar kan geen code
    uitvoeren, zoals een SVG zonder scripts, een beschadigde afbeelding of een
    bestand dat ontbreekt in de opslag. Ook afbeeldingen die verder in orde
    zijn, maar zijn geüpload door iemand die nu geen actieve medewerker is.
  * ``OK``: voldoet aan de uploadvalidatie en is geüpload door een actieve
    medewerker.

  Standaard toont het commando een tabel met alleen de afbeeldingen die
  aandacht nodig hebben, de ernstigste eerst, met per afbeelding het ID, de
  uploaddatum, de uploader, de bestandsnaam, de reden en een link naar de
  admin. De samenvatting wordt naar stderr geschreven. Met ``--all`` worden ook
  de afbeeldingen getoond die in orde zijn. Gebruik ``--format csv --output
  <bestand>`` voor een volledig overzicht van alle afbeeldingen, inclusief de
  URL van het bestand. Kan het commando de admin- en bestands-URL's niet
  volledig maken, geef dan het domein mee met
  ``--base-url https://<domein>/``.

  Het commando eindigt met exitcode ``3`` als er verdachte afbeeldingen zijn,
  en anders met exitcode ``4`` als er afbeeldingen niet konden worden
  gecontroleerd. Exitcode ``1`` betekent dat het commando is mislukt.

  **Alleen als de virusscan (ClamAV) is ingeschakeld** in de algemene
  configuratie, kunt u de afbeeldingen daarnaast op virussen scannen. Geef
  hiervoor de validator van Open Inwoner mee aan hetzelfde commando:

  .. code-block:: bash

      python src/manage.py check_filer_images \
          --validator open_inwoner.utils.virus_scan.filer_image_virus_validator

  Geïnfecteerde afbeeldingen, en afbeeldingen die niet konden worden gescand,
  worden dan als ``SUSPICIOUS`` gemarkeerd, met de naam van het virus of de
  foutmelding als reden. Gebruik ``--validator`` alleen als de virusscan is
  ingeschakeld en ClamAV bereikbaar is: anders stopt het commando met een
  foutmelding (bijvoorbeeld ``CommandError: Virus scanning is not enabled in
  the site configuration.``) en exitcode ``1``, zonder rapport. Valt ClamAV
  tijdens het controleren weg, dan worden alle afbeeldingen die daarna nog
  worden gecontroleerd als ``SUSPICIOUS`` gemarkeerd, met de reden
  ``Could not be scanned: ...``. Herstel in dat geval de verbinding met ClamAV
  en voer het commando opnieuw uit.

  ``check_filer_images`` controleert alleen afbeeldingen. Scan met de virusscan
  ingeschakeld ook alle overige filer-bestanden:

  .. code-block:: bash

      python src/manage.py scan_filer_files

  Als er geen virussen worden gevonden, toont dit
  ``Scanned N items and no viruses found``. Anders toont het per bestand het
  ID, de bestandsnaam, de URL en het resultaat van de scan, en eindigt het
  commando met exitcode ``1``. Is de virusscan niet ingeschakeld of is ClamAV
  niet bereikbaar, dan eindigt het met exitcode ``2``.

  Bekijk vervolgens alle afbeeldingen met ``SUSPICIOUS`` en ``UNCHECKED``:

  * Open deze bestanden **niet** in een browser waarin u bent ingelogd op
    Open Inwoner, ook niet via de link naar het bestand in de admin. Download
    ze bijvoorbeeld met ``curl -o <bestand> <URL>`` (zonder sessiecookie) en
    bekijk ze in een teksteditor.
  * Bij SVG-bestanden: let op ``<script>``-elementen, event handlers (zoals
    ``onload=`` of ``onclick=``), ``javascript:``-links, ``<foreignObject>``,
    ``<iframe>``, ingebedde HTML en verwijzingen naar externe bronnen.
  * Bij niet-afbeeldingen: controleer wat voor bestand het werkelijk is
    (bijvoorbeeld met ``file <bestand>``). HTML-, JavaScript- en andere
    bestanden die geen echte afbeelding zijn, horen hier niet thuis.
  * Bestanden die via de editor zijn geüpload, staan in de filer-admin onder
    "Unsorted Uploads" en hebben de uploadende gebruiker als eigenaar. Een
    eigenaar die geen medewerker (staff) is, wijst op misbruik.

  Verwijder bestanden die geen echte afbeelding zijn via de filer-admin en
  controleer of ze ook uit de opslag (``MEDIA_ROOT/filer_public/``) en uit een
  eventuele CDN of cache zijn verwijderd. Controleer ook de access logs op
  ``POST``- en ``PATCH``-verzoeken naar ``/prosemirror/filer-image-upload/``
  en op onverwacht gewijzigde namen, beschrijvingen en bijschriften van
  afbeeldingen. Zijn er aanwijzingen dat een beheerder een geüpload bestand
  heeft geopend, beschouw dat account dan als gecompromitteerd: beëindig de
  sessies, reset het wachtwoord en de 2FA, en roteer de geheimen die in de
  admin zichtbaar zijn.
* Uploaden en bewerken van afbeeldingen in de editor is nu beperkt tot
  medewerkers (staff) met de permissies ``filer.add_image`` (uploaden) en
  ``filer.change_image`` (bewerken). Zorg dat de groepen van redacteuren die
  producten en categorieën beheren deze permissies hebben.
* In de editor kunnen alleen nog JPEG-, PNG-, GIF- en WebP-afbeeldingen van
  maximaal 10 MiB worden geüpload. De inhoud van het bestand moet passen bij
  de extensie. SVG-bestanden kunnen niet meer via de editor worden geüpload.

Nieuwe features
---------------

* Nieuw management commando ``scan_filer_files``, dat alle filer-bestanden
  (inclusief afbeeldingen) met de bestaande ClamAV-integratie op virussen
  scant.
* Nieuwe validator ``open_inwoner.utils.virus_scan.filer_image_virus_validator``
  voor het commando ``check_filer_images``, die afbeeldingen met de bestaande
  ClamAV-integratie op virussen scant.

Onderhoud
---------

* ``maykin-django-prosemirror`` bijgewerkt naar versie ``0.11.0``.

2.4.5 (2026-09-29)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.5`.

Bugfixes
--------

* [:gh:`2878`]: Een via het contactformulier gestelde vraag (OpenKlant2) werd
  niet getoond op de 'Mijn vragen'-pagina als het aanmaken van de interne taak
  mislukte, omdat de vragencache dan niet werd ververst. De vraag wordt nu
  geregistreerd en de cache ververst, ongeacht of het aanmaken van de interne
  taak slaagt. Fouten bij het aanmaken van de interne taak en bij het
  registreren van een vraag worden nu gelogd.

2.4.4 (2026-09-28)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.4`.

Deployment aandachtspunten
--------------------------

* [:gh:`2847`]: ``django-cms`` is bijgewerkt van ``4.1.10`` naar ``5.0.11``
  (nieuwe major versie). Controleer na de upgrade of CMS-pagina's, de
  paginaboom en het bewerken/publiceren van pagina's in het beheerscherm
  correct werken. Herbouw daarnaast de zoekindex
  (``python src/manage.py search_index --rebuild``), zodat paginatitels in de
  zoekresultaten correct worden weergegeven.
* [:gh:`2831`] / [:gh:`2832`]: De webserver wordt niet langer met
  ``--lazy-apps`` gestart, zodat OpenTelemetry nu ook voor de webcontainer
  werkt. Daarnaast wordt de standaard ``OTEL_SERVICE_NAME`` per rol
  (``openinwoner-web``, ``openinwoner-celery-worker``,
  ``openinwoner-celery-beat``, ``openinwoner-celery-monitor``) nu daadwerkelijk
  gezet in plaats van één generieke ``openinwoner``. Dashboards of alerts die
  filteren op de service-naam ``openinwoner`` moeten mogelijk worden aangepast.

Nieuwe features
---------------

* [:gh:`2784`]: Parallelle ZGW-verzoeken (o.a. het ophalen en resolven van
  zaken, formulieren en het opwarmen van de ZGW-cache) respecteren nu
  daadwerkelijk de ingestelde timeout: taken die bij het verstrijken van de
  timeout nog niet zijn gestart worden geannuleerd in plaats van alsnog
  uitgevoerd, en resultaten van taken die net na de timeout klaar zijn worden
  niet langer weggegooid.

Bugfixes
--------

* [:gh:`2807`]: Bij een statusnotificatie voor een zaak met meerdere
  betrokkenen werd de verwerking voor alle gebruikers afgebroken zodra één
  gebruiker zich had afgemeld voor notificaties. Afgemelde gebruikers worden
  nu overgeslagen.
* [:gh:`2852`]: Het toevoegen, wijzigen of verwijderen van niet-standaard
  digitale adressen (e-mail/telefoon) in het profiel werd niet doorgezet naar
  OpenKlant. Dit is hersteld.
* [:gh:`2793`]: De synchronisatie vanuit OpenKlant kon een ``IntegrityError``
  geven wanneer het oude standaard e-mailadres of telefoonnummer was
  verwijderd en OpenKlant tegelijkertijd een ander adres als standaard had
  aangewezen.
* [:gh:`2776`]: ``RenderableTag`` is beveiligd tegen template-injectie:
  argumentwaarden worden niet langer in de template-broncode geïnterpoleerd
  maar via de template-context doorgegeven.
* [:gh:`2789`]: Fouten bij het resolven van gerelateerde ZGW-objecten (rol,
  zaaktype, status, statustype, resultaat, resultaattype) worden nu per object
  gelogd en gerapporteerd. Ook zoekresultaten melden deze fouten nu, zodat een
  onvolledig resultaat de waarschuwingsbanner toont.
* [:gh:`2786`]: De cache-sleutel voor zaken van bedrijven houdt nu rekening met
  de instelling ``use_openzaak_120_params``; voorheen werden na het wijzigen van
  deze instelling tot het verlopen van de cache nog zaken getoond die met de
  oude parameters waren opgehaald.
* [:gh:`2847`]: Paginatitels van CMS-pagina's werden na de ``django-cms``
  upgrade inclusief paginapad (bijv. ``Foo (/foo)``) geïndexeerd en zo in de
  zoekresultaten getoond. Dit is gecorrigeerd.
* [:gh:`2594`]: Verbeterde foutafhandeling in de setup-configuration stappen
  voor Open Zaak en OpenKlant2. In de Docker Compose-setup wacht de
  ``web``-service nu tot ``setup_configuration`` succesvol is afgerond.
* [:gh:`2747`]: De pijl in de "Ga naar"-plugin wordt nu via flexbox uitgelijnd
  in plaats van met absolute positionering.
* [:gh:`2957`]: De ruimte tussen de vraag- en antwoordsecties op de
  vraagdetailpagina is verkleind.

Onderhoud
---------

* [:gh:`2847`]: ``django-cms`` bijgewerkt naar versie ``5.0.11``.
* [:gh:`2625`]: ``django-treebeard`` bijgewerkt naar versie ``5.3.1``
  (voorheen ``4.4``). De beheerschermen voor categorieën en vragenlijsten en
  het in-/uitklappen van de boomstructuur in het beheer zijn hierop aangepast.
* [:gh:`2174`]: PDF-export maakt nu gebruik van de PDF-rendering uit
  ``maykin-common`` (bijgewerkt naar ``0.21.0``) in plaats van ``weasyprint``
  direct; ``weasyprint`` is daarmee bijgewerkt naar ``70.0``.
* [:gh:`2868`]: ``djangorestframework`` bijgewerkt naar versie ``3.18.0``.
* [:gh:`2819`]: ``sqlparse`` bijgewerkt naar versie ``0.6.0``.
* [:gh:`2810`]: ``tablib`` bijgewerkt naar versie ``3.10.0``.
* [:gh:`2747`]: ``@open-inwoner/design-tokens`` bijgewerkt naar versie ``0.0.33``.

2.4.3 (2026-08-11)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.3`.

Nieuwe features
---------------

* [:gh:`2736`]: De 'Mijn vragen'-pagina's zijn versneld door contactmomenten
  parallel op te halen (eSuite), klantcontacten server-side te filteren op
  partij (OpenKlant) en listings/resolved contactmomenten/partij-uuid te
  cachen; een onvolledig resultaat toont nu een waarschuwingsbanner met
  retry-link in plaats van alleen een foutmelding.

2.4.2 (2026-08-10)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.2`.

Bugfixes
--------

* [:gh:`2735`]: Onvolledige zakenlijsten (door een timeout of fetch-/ resolutiefout bij
  het ophalen) worden nu herkend en gemeld in plaats van stilzwijgend als 'geen zaken'
  getoond. De zakenlijst, de zaken-plugin en de zoekfunctie tonen bij een onvolledig
  resultaat een waarschuwing en proberen automatisch opnieuw zaken op te halen, met een
  handmatige retry-link als dat niet lukt.
* [:gh:`2728`]: Links in ProseMirror-tekstvelden (bijv. FAQ-antwoorden,
  categorie- en productbeschrijvingen) staan nu alleen nog http(s)-, mailto-,
  tel- of relatieve/fragment-URL's toe bij het renderen.
* [:gh:`2623`]: Het vraagveld in het admin-overzicht van
  ``QuestionnaireStepAdmin`` wordt nu correct geëscaped.
* [:gh:`2745`]: Een homepage-plugin met ``hx-trigger="load"`` (zoals 'Mijn
  Zaken') kon na terug/vooruit-navigatie via de back/forward cache (bfcache)
  blijven hangen op de laadanimatie, omdat het ``load``-event dan niet
  opnieuw afgaat. De pagina wordt nu automatisch herladen wanneer dit
  gebeurt.
* [:gh:`2745`]: Een formulierkaart op de homepage zonder vervolglink
  herlaadde de pagina bij een klik (leeg ``href``). Deze wordt nu als
  niet-interactief weergegeven.
* [:gh:`2765`]: Taakparameters voor de notificatie-collectors (in de context
  van plannen/acties) bevatten een niet-serialiseerbaar argument, wat in
  productie een fout gaf maar in tests onopgemerkt bleef. Hersteld.
* [:gh:`2764`]: De geconfigureerde service-timeout wordt nu ook toegepast op
  de OpenKlant2-client; voorheen werd geen timeout doorgegeven aan
  verzoeken.
* [:gh:`2740`]: Ruimte tussen de kop en het statuslabel in de filterpopup
  hersteld.
* [:gh:`2733`]: Enkele CMS-beheerteksten (bijv. bij het verwijderen van een
  pagina) werden door een upstream vertaalfout in ``django-cms`` in het Duits
  weergegeven i.p.v. het Nederlands. Deze teksten worden nu lokaal
  overschreven met de juiste Nederlandse vertaling.
* [:gh:`2736`]: Een niet-gevonden vraag- of contactmoment-uuid gaf een
  500-fout in plaats van een 404 bij het doorverwijzen vanuit een
  klantcontactmoment-notificatie en bij het opzoeken van een vraag in
  OpenKlant.

Onderhoud
---------

* [:gh:`2759`]: ``Django`` bijgewerkt naar versie ``5.2.17``.
* [:gh:`2731`]: ``leaflet`` bijgewerkt naar versie ``1.9.4`` (voorheen
  ``1.7.1``); de verouderde, ongebruikte vendored ``_leaflet.scss`` is
  verwijderd.
* ``cryptography`` bijgewerkt naar versie ``50.0.0``, ``pillow`` naar
  ``12.3.0`` en ``pyopenssl`` naar ``26.4.0``.
* Frontend dependencies bijgewerkt, o.a. ``vitest``, ``immutable`` en ``shell-quote``.
* ``maykin-django-prosemirror`` bijgewerkt naar versie ``0.9.0``.

2.4.1 (2026-07-22)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.1`.

Bugfixes
--------

* ``maykin-common`` bijgewerkt naar ``0.20.1``; dit verhelpt 500-fouten
  bij healthchecks op Kubernetes.

2.4.0 (2026-07-20)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.4.0`.

Deployment aandachtspunten
--------------------------

* [:gh:`2476`]: De omgevingsvariabelen ``ZGW_CASE_LIST_NUM_WORKERS``,
  ``ZGW_CASE_LIST_FETCH_TIMEOUT``, ``CACHE_ZGW_ZAKEN_TIMEOUT`` en
  ``CACHE_ZGW_CATALOGI_TIMEOUT`` worden bij de migratie eenmalig
  rechtstreeks uit de omgeving gelezen om de nieuwe configuratievelden op
  ``OpenZaakConfig``/``ZGWApiGroupConfig`` te initialiseren. Laat deze
  variabelen staan tot na de migratie; ze kunnen daarna worden verwijderd,
  waarna de waarden alleen nog via de beheeromgeving instelbaar zijn.
* [:gh:`1900`]: De omgevingsvariabele ``ZGW_LIMIT_NOTIFICATIONS_FREQUENCY``
  is vervallen. Anders dan bij de ZGW-verbindingsparameters hierboven wordt
  een eventueel aangepaste waarde niet automatisch overgenomen: het nieuwe
  veld ``OpenZaakConfig.notification_frequency_limit`` krijgt altijd de
  standaardwaarde van 900 seconden. Was deze omgevingsvariabele aangepast,
  stel de gewenste waarde na de upgrade opnieuw in via de beheeromgeving.
* [:gh:`1900`]: Webhooknotificaties worden niet langer synchroon in het
  request verwerkt, maar eerst opgeslagen als ``NotificationRecord`` en
  daarna via Celery afgehandeld. Een draaiende Celery-worker is dus
  vereist voor de verwerking van notificaties; zonder worker stapelen
  onverwerkte records zich op. Retentietermijnen en maximale
  payload-grootte zijn instelbaar via de beheeromgeving
  (``NotificationProcessingConfig``).
* [:gh:`1900`]: Een nieuwe periodieke Celery-taak ('Opschonen
  notificatieberichten', dagelijks om 03:00) ruimt oude
  ``NotificationRecord``-rijen op. Dit vereist een draaiende celery-beat
  service. Voor handmatig gebruik is ook een management command
  ``prune_notification_records`` beschikbaar.
* [:gh:`2611`, :gh:`2615`]: Deze release bevat datamigraties (rij-voor-rij,
  geen bulkoperaties) die voor elke bestaande gebruiker met een
  e-mailadres of telefoonnummer een ``DigitalAddress``-record aanmaken.
  Houd op installaties met veel gebruikers rekening met een langere
  migratieduur tijdens de deploy.
* [:gh:`2589`]: Nieuwe omgevingsvariabelen ``ELASTICSEARCH_DSL_AUTOSYNC``
  en ``ELASTICSEARCH_DSL_AUTO_REFRESH`` (standaard: ``True``; dit komt
  overeen met het bestaande gedrag). Zet ``ELASTICSEARCH_DSL_AUTOSYNC`` op
  ``False`` wanneer Elasticsearch niet gegarandeerd beschikbaar is, om
  500-fouten bij beheeracties te voorkomen; de zoekindex wordt dan alleen
  bijgewerkt via de periodieke Celery-taak.
* [:gh:`2502`]: Welke documentstatussen zichtbaar zijn voor gebruikers
  ('in bewerking', 'ter vaststelling', 'definitief', 'gearchiveerd') is nu
  instelbaar via ``OpenZaakConfig`` in de beheeromgeving. De
  standaardwaarde ('definitief' en 'gearchiveerd') komt overeen met het
  bestaande gedrag; er is geen actie nodig. Let op: een lege selectie
  schakelt het filteren op status volledig uit, waardoor documenten met
  elke status zichtbaar worden.
* [:gh:`2507`]: De labels op het zaakdetail-dashboard ('Zaaknummer',
  'Zaak ingediend op', 'Besluit genomen op', 'U ontvangt een besluit
  vóór') zijn nu aanpasbaar via ``OpenZaakConfig`` in de beheeromgeving
  (fieldset 'Zaakdetail dashboard labels'). De standaardwaarden komen
  overeen met de bestaande teksten; er is geen actie nodig.
* [:gh:`2662`]: Nieuwe (vervallen) omgevingsvariabele
  ``OIDC_USE_LEGACY_ENDPOINTS`` (standaard: ``True``; dit komt overeen met
  het bestaande gedrag). Hiermee wordt nog steeds de legacy
  per-provider OIDC-callback-URL (bv. ``/digid-oidc/callback/``) als
  ``redirect_uri`` doorgegeven aan de IdP, in plaats van het generieke
  ``/oidc/callback/`` endpoint. Zet deze variabele op ``False`` zodra de
  whitelist bij elke IdP is bijgewerkt naar het generieke endpoint; de
  instelling wordt in een latere release verwijderd.

Nieuwe features
---------------

* Meerdere digitale adressen: gebruikers kunnen meerdere e-mailadressen en
  telefoonnummers beheren en er per type één als primair markeren.

  - [:gh:`2611`]: Nieuw model ``DigitalAddress`` en
    ``User.preferred_address`` toegevoegd als basis voor het beheer van
    meerdere digitale adressen per gebruiker.
  - [:gh:`2615`]: Het telefoonnummer en e-mailadres van de gebruiker worden
    nu gesynchroniseerd met de bijbehorende ``DigitalAddress``; het aparte
    alternatieve telefoonnummerveld is vervangen door een niet-standaard
    ``DigitalAddress``.
  - [:gh:`2612`]: Digitale adressen worden nu in beide richtingen
    gesynchroniseerd met OpenKlant (OpenKlant is bepalend voor adressen die
    daar al bestaan). OTEL-metrics toegevoegd om deze synchronisatie te
    monitoren.
  - [:gh:`2613`]: Digitale adressen worden nu ook gesynchroniseerd met
    eSuite.
  - [:gh:`2593`]: Front-end voor het beheren van meerdere e-mailadressen en
    telefoonnummers op de profielpagina (gedeeltelijke implementatie). Bij
    het verwijderen van een lokaal digitaal adres wordt het bijbehorende
    adres nu ook bij OpenKlant verwijderd.
  - [:gh:`2628`]: Formset voor digitale adressen toegevoegd aan de
    profielbewerkpagina.
  - [:gh:`2656`]: Voorkeursadres (``preferred_address``) toegevoegd aan de
    profielbewerk- en weergavepagina's.
  - [:gh:`2652`]: Alle digitale adressen worden nu getoond op de
    profielweergavepagina, met het standaardadres bovenaan.
  - [:gh:`2691`]: De keuzelijst voor het algemene voorkeursadres ('Voorkeur
    digitaal adres') is weer verwijderd uit het profiel totdat het beoogde
    gebruik is verduidelijkt.
  - ``DigitalAddress`` toegevoegd als inline in de Django admin.
  - [:gh:`2698`]: Het e-mailadres uit registratie wordt nu ook opgeslagen
    als ``DigitalAddress``, zodat het niet leeg blijft op de profielpagina
    en wordt gesynchroniseerd met OpenKlant.
  - [:gh:`2618`]: Bij een API-syncfout tijdens het bewerken van het profiel
    gaat de gebruiker terug naar de bewerkpagina (met foutmelding) i.p.v.
    de detailpagina; eSuite-fouten worden hierbij niet langer stilzwijgend
    onderdrukt.
  - [:gh:`2636`]: E-mailadressen en telefoonnummers worden nu al bij de
    eerste invoer op formaat gevalideerd (voorheen pas nadat het adrestype
    was ingesteld).
  - [:gh:`2508`]: E-mailadressen en telefoonnummers worden genormaliseerd
    voor vergelijking, zodat ze niet onterecht als duplicaat worden
    aangemaakt.
  - [:gh:`2655`]: Formset-brede validatiefouten (bijv. een dubbel adres)
    worden nu getoond onder de 'toevoegen'-knop i.p.v. stilzwijgend
    genegeerd.

* Leestekens in namen toegestaan: namen als ``'t Hart`` worden nu
  geaccepteerd en leiden niet langer tot een validatiefout.

  - [:gh:`2510`]: De validatie van voornaam, tussenvoegsel en achternaam is
    verplaatst van het model naar de formulierlaag, zodat namen met
    leestekens en diakritische tekens vanuit de BRP weer verwerkt kunnen
    worden.

* Omgevingsvariabelen gedocumenteerd: de omgevingsvariabelen die
  beschikbaar zijn voor de configuratie worden nu toegelicht in de
  documentatie.

  - [:gh:`2548`]: ``maykin-common`` bijgewerkt naar ``0.19.0`` en
    ``django-health-check`` naar ``4.4.1``; de lokale ``config()``-wrapper
    is vervangen door ``maykin_common.config``, en omgevingsvariabelen zijn
    gedocumenteerd (zie ``02_env_vars.rst``).

* [:gh:`2676`]: De container-tabel in Mijn Afval toont nu het openbare
  container-ID in plaats van het interne API-ID.
* [:gh:`2669`]: Ophaaldata in Mijn Afval tonen de weekdag nu verkort (bijv.
  'ma' i.p.v. 'maandag').
* [:gh:`2631`]: Ledigingskosten worden nu getoond in Mijn Afval.
* [:gh:`2417`]: Vertalingen en weergavestructuur van de KVK-filiaalkiezer
  verbeterd.
* [:gh:`2476`]: Verbindingsparameters voor ZGW (aantal workers, timeouts,
  cache-timeouts) zijn verplaatst van omgevingsvariabelen naar
  configuratievelden in de admin (``OpenZaakConfig`` /
  ``ZGWApiGroupConfig``), zodat deze per API-groep en zonder herstart
  aangepast kunnen worden. De bijbehorende omgevingsvariabelen zijn
  verwijderd.
* [:gh:`2502`]: Zichtbare documentstatussen (bijv. 'definitief',
  'gearchiveerd') zijn nu configureerbaar via ``OpenZaakConfig``.
* [:gh:`2490`]: Zoekveld voor volledig zaaknummer toegevoegd aan de Mijn
  Zaken-filters.
* [:gh:`2487`]: NL Design System-klasse (``.nl-paragraph``) toegevoegd aan
  ProseMirror-paragrafen.
* [:gh:`2507`]: Labels op het zaakdetail-dashboard (identificatie, start-,
  eind- en verwachte einddatum) zijn nu configureerbaar via
  ``OpenZaakConfig``.
* [:gh:`1900`]: Verwerking van webhooknotificaties is losgekoppeld van de
  ontvangst: binnenkomende notificaties worden eerst duurzaam opgeslagen
  en vervolgens via Celery verwerkt, met locking, retries en opschoning
  van oude records. Bijbehorende admin-omgeving toegevoegd.

Bugfixes
--------
* Vraag bij een zaak correct gekoppeld: een vraag die vanuit een zaak
  gesteld werd, kon in OpenKlant ten onrechte als 'anoniem' geregistreerd
  staan.

  - [:gh:`2663`]: Vragen worden nu aan een zaak gekoppeld via het
    zaak-UUID i.p.v. de identificatie, zodat de koppeling niet verloren
    gaat bij wijzigende identificaties.
  - [:gh:`2663`]: VCR-cassettes voor OpenKlant-tests hersteld.

* Dubbele vestigingen bij eSuite werken weer: als een vestigingsnummer
  meerdere keren voorkwam, gaf eSuite een conflict (409) terug, waardoor
  e-mailadres en telefoonnummer niet opgehaald of aangepast konden worden.

  - [:gh:`2661`]: KvK-nummer en vestigingsnummer worden nu samen
    meegestuurd naar eSuite, zodat gelijke vestigingsnummers niet als
    conflict (409) worden afgewezen.

* Zoeken op zaaknummer respecteert nu de rolconfiguratie: bij het zoeken op
  een volledig zaaknummer werd uitsluitend op het rolfilter van de API
  vertrouwd. Omdat eSuite filterparameters kan negeren, konden de gegevens
  van een zaak in de zoekresultaten zichtbaar worden voor een betrokkene
  zonder de ingestelde rol (``limit_user_visible_cases_to_role``). De zaak
  zelf was niet toegankelijk; het ging om de gegevens in de zoekresultaten.

  - [:gh:`2659`]: De rolcontrole van de zaakdetailpagina wordt nu ook
    toegepast bij het zoeken, zowel in Mijn Zaken als in het algemene
    zoekveld. Kan de rol niet worden opgehaald, dan wordt de zaak niet
    getoond.
  - [:gh:`2665`]: Cachesleutels voor de zakenlijst houden nu rekening met de
    vertrouwelijkheids- en rolconfiguratie, zodat wijzigingen niet meer
    verouderde cache-resultaten tonen.

* [:gh:`2684`]: ``zgw_import_data`` breekt niet langer volledig af bij
  gedeeltelijke API- of database-fouten (de strengere foutafhandeling uit
  :gh:`2581` is teruggedraaid).
* [:gh:`2673`]: Document-eigendom wordt nu afgedwongen bij het downloaden
  van bestanden via de inbox. Met dank aan `@Santoshkumarpuppala
  <https://github.com/Santoshkumarpuppala>`_ en `White Hat Security
  <https://www.whitehatsecurity.nl/>`_ voor het rapporteren van dit
  issue.
* [:gh:`2619`]: Celery health checks zijn gemigreerd naar de
  implementatie uit maykin-common 0.19.0 (de oude implementatie bevatte
  een padfout waardoor de check nooit slaagde).
* [:gh:`2573`]: ProseMirror-tekst miste soms de juiste render-/cms-tags,
  waardoor de ``nl-paragraph``-klasse niet werd toegepast. Hersteld.
* [:gh:`2520`]: Bij een niet-200 response op de zaakdetailpagina (via
  HTMX) wordt nu een foutmelding getoond i.p.v. niets.
* [:gh:`2250`]: Verticale uitlijning van knoppen in inline-flex
  containers gecorrigeerd.

Onderhoud
---------

* Update OIDC library:

  - [:gh:`2662`]: ``mozilla-django-oidc-db`` en ``django-digid-eherkenning``
    bijgewerkt naar de nieuwe generieke ``OIDCClient``/``OIDCProvider`` +
    plugin-architectuur (in plaats van de losse per-provider
    configuratiemodellen).
  - [:gh:`2662`]: OIDC-integratie (backends, callback-/logout-views,
    registratie) aangepast aan de nieuwe plugin-architectuur.
  - [:gh:`2662`]: OIDC-tests aangepast aan de plugin-architectuur.
  - [:gh:`2662`]: Admin-OIDC-flowtests overgezet naar een
    ``OIDCClientFactory`` in plaats van het mocken van de verwijderde
    configuratiemodellen.
  - [:gh:`2662`]: DigiD-OIDC-flowtests overgezet naar de
    ``OIDCClientFactory``.
  - [:gh:`2662`]: eHerkenning-OIDC-flowtests overgezet naar de
    ``OIDCClientFactory``.
  - [:gh:`2662`]: eIDAS-OIDC-flowtests overgezet naar de ``OIDCClientFactory``.
  - [:gh:`2662`]: Aangepast aan de ``STORAGES``-configuratie van
    django-privates 4.x (in plaats van de vervallen ``PRIVATE_MEDIA_*``
    -instellingen).
  - [:gh:`2662`]: OIDC-flows van de lokale Keycloak dev-stack geseed en
    bekabeld via ``setup_configuration`` en docker compose.
  - [:gh:`2678`]: ``zgw-consumers`` bijgewerkt van ``0.38.1`` naar ``2.0.2``.
  - [:gh:`2662`]: Nieuwe (vervallen) instelling ``OIDC_USE_LEGACY_ENDPOINTS``
    toegevoegd om de legacy per-provider OIDC-callback-URL's uit te kunnen
    zetten zodra de whitelist bij de IdP is bijgewerkt.
  - E2e-tests (Playwright) toegevoegd voor de OIDC-inlogflows (DigiD,
    eHerkenning, eIDAS, admin) tegen een live Keycloak.
  - eHerkenning-rechtspersoon testgebruiker toegevoegd aan de
    Keycloak-testrealm.
  - Playwright-video-opnames worden nu correct afgerond en benoemd (voorheen
    bleven het 0-byte bestanden).

* Verschillende bibliotheken bijgewerkt:

  - [:gh:`2651`]: ``shell-quote`` vastgepind op ``1.8.4``.
  - [:gh:`2650`]: ``webob`` bijgewerkt naar ``1.8.10``.
  - [:gh:`2649`]: ``vcrpy`` bijgewerkt naar ``8.2.1``.
  - [:gh:`2648`]: ``PyJWT`` bijgewerkt naar ``2.13.0``.
  - [:gh:`2646`]: ``cryptography`` bijgewerkt naar ``48.0.1``.
  - [:gh:`2552`]: ``log-outgoing-requests`` bijgewerkt naar ``0.9.1``.
  - [:gh:`2563`]: ``vitest`` bijgewerkt naar ``4.1.8`` en ``storybook`` naar
    ``10.4.1``.

* CI-workflows aangepast:

  - ``setup-django-backend`` CI-action bijgewerkt naar ``1.4.1``.
  - CodeQL-actions vastgepind.
  - ``pre-commit/action`` (niet toegestaan in de organisatie-allowlist)
    vervangen door een directe pre-commit-aanroep.
  - Ubuntu-versie in ``readthedocs.yml`` bijgewerkt naar ``24.04``.
  - Python-versie in de CodeQL-workflow nu expliciet ingesteld vanuit
    ``pyproject.toml`` (voorkomt parse-fouten door een verouderde
    runner-Python).

* Conventional commits / commitizen aangepast:

  - Conventional-commit validatie aangescherpt: ``fixup!``/``squash!``/
    ``amend!``-prefixes worden niet langer toegestaan.
  - Commitizen bump-instellingen aangepast om alle versiestrings te
    herkennen.

* E2e-tests toegevoegd voor het bewerken van het profiel.
* [:gh:`2582`]: ``django-prosemirror`` bijgewerkt naar ``0.8.0`` (loste op
  dat dynamisch toegevoegde formsetrijen in de admin geen werkende
  ProseMirror-editor kregen).
* CI-controle van commitberichten gebruikt nu de PR head SHA i.p.v. de
  merge-commit SHA.
* [:gh:`2589`]: ``ELASTICSEARCH_DSL_AUTOSYNC``/``AUTO_REFRESH``-instellingen
  geconsolideerd in de basisconfiguratie.
* [:gh:`2561`]: Dependency-compilatiejobs samengevoegd in één CI-matrix;
  ``pip-tools`` vervangen door de via ``uv`` gebundelde versie.
* [:gh:`2190`]: Commitizen geconfigureerd voor conventional commits
  (pre-commit hook + CI-validatie); CONTRIBUTING bijgewerkt;
  ``charset-normalizer`` naar ``3.4.4`` en ``packaging`` naar ``26.0``.

Oudere versies staan in het changelog-archief (``CHANGELOG_ARCHIVE.rst``).
