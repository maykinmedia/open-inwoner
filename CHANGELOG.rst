2.0.0 (2025-XX-XX) [UNRELEASED]
===============================

Voor een volledig overzicht van alle commits, zie ...

Deployment aandachtspunten
--------------------------

* OpenTelemetry ondersteuning is toegevoegd voor metrics en logging. De applicatie kan nu
  telemetrie data exporteren naar een OpenTelemetry collector via gRPC. Configuratie gebeurt
  via omgevingsvariabelen zoals gedocumenteerd in de `OpenTelemetry specificatie
  <https://opentelemetry.io/docs/specs/otel/configuration/sdk-environment-variables/#general-sdk-configuration>`_.
  Belangrijke variabelen zijn:

  - ``OTEL_SDK_DISABLED`` (standaard: ``true``) - Zet op ``false`` om OpenTelemetry te activeren
  - ``OTEL_EXPORTER_OTLP_ENDPOINT`` - gRPC endpoint van de OpenTelemetry collector (bijv. ``http://otel-collector:4317``)
  - ``OTEL_EXPORTER_OTLP_HEADERS`` - Optionele headers voor authenticatie (bijv. ``Authorization=Basic ...``)
  - ``OTEL_EXPORTER_OTLP_METRICS_INSECURE`` (standaard: ``true``) - Sta onveilige verbindingen toe voor development

  De OpenTelemetry SDK is standaard uitgeschakeld en moet expliciet worden geactiveerd per
  deployment. De applicatie verwacht een gRPC OpenTelemetry collector endpoint.
* De YAML structuur van ``django-setup-configuration`` voor het configureren van het
  klantensysteem is aangepast. De nieuwe structuur is omschreven in de `documentatie
  <https://docs.openinwoner.nl/en/latest/configuration/index.html>`_.
* De vervanging van CKEditor door Prosemirror vereiste het converteren van gegevens in HTML en
  markdown naar een nieuwe structuur. In sommige gevallen (vooral wanneer de gegevens tabellen
  of andere geavanceerde elementen bevatten) is de opmaak mogelijk niet behouden gebleven. In
  deze gevallen blijft de ruwe inhoud van de oorspronkelijke CKEditor behouden zonder opmaak.
  Controleer de opmaak van de inhoud van de rich text editor, met name voor de onderwerpen en
  de producten.
* De database migraties, die tijdens het deployen eenmalig zullen worden uitgevoerd,
  kunnen langer duren dan normaal voor installaties met een groot aantal gebruikers. Dit
  is een gevolg van nieuwe database indices die zijn toegevoegd in het kader van de de
  nieuwe eIDAS ondersteuning.

Nieuwe features
---------------

* [:taiga-us:`3478`, :pr:`1953`]: Extra OpenTelemetry metrics toegevoegd voor
  account- en profiel gerelateerde acties, zoals aanmeldingen, registraties,
  uitnodigingen en profielwijzigingen.
* [:taiga-us:`3461`, :taiga-ta:`3473`, :pr:`1932`]: Basisinfrastructuur voor
  OpenTelemetry toegevoegd, inclusief logging en metrics ondersteuning voor
  observability.
* [:taiga-us:`3408`, :pr:`1881`]: Nieuw selectiescherm voor eHerkenning-inlog met zoek-
  en dropdownfunctie voor betere UX waarmee gewiseld kan worden tussen vestigingen.
* [:taiga-us:`3450`, :taiga-ta:`3454`]: CKEditor wordt vervangen door Prosemirror
* [:taiga-us:`3408`, :pr:`1948`]: Het selectiescherm voor eHerkenning-inlog met zoek-
  en dropdownfunctie aan Storybook toegevoegd.
* [:taiga-us:`3499`, :pr:`1962`]: WCAG toegankelijkheidsverbeteringen op de Profiel pagina
  en de zakenoverzichtspagina.
* [:taiga-us:`3492`, :pr:`1960`, :pr:`2001`]: Header en logo zijn verkleind; onderwerpen en zoekveld
  zijn omgewisseld op desktop; mobiele navigatie omgezet naar een overlay; mobiele welkomsttekst hoger
  geplaatst; welkomsttekst wordt nu los onder de bannerafbeelding weergegeven op desktop.
* [:taiga-us:`3508`, :pr:`1979`]: Alle logging aangepast om gebruikt te maken van ``structlog``,
  waardoor de logging data beter kan worden verwerkt door andere observability tools zoals
  Grafana.
* [:taiga-us:`3519`, :pr:`1981`]: Nieuw design van openstaande acties plugin op de
  homepagina geïmplementeerd.
* [:taiga-is:`3556`, :pr:`1995`]: Uitgaande requests worden nu gelogd als gestructureerde
  events met ``structlog``, waardoor ze beter verwerkt kunnen worden door observability tools.
* [:taiga-us:`3512`, :pr:`2003`]: De taken die worden weergegeven onder 'Openstaande acties' en
  'Mijn taken' zijn nu samengevoegd en worden nu samen weergegeven onder 'Mijn taken'.
* [:taiga-is:`3321`, :pr:`2008`]: Dubbele links in sitemap verwijderd.
* [:taiga-us:`3510`, :pr:`1988`, :pr:`2002`]: CMS-plugin toegevoegd voor links naar andere
  portalen van de gemeente.
* [:taiga-us:`3511`, :taiga-is:`3583`, :taiga-is:`3531`, :pr:`1996`, :pr:`2022`]: Front-end voor CMS-plugin
  voor links naar andere portalen gebouwd, inclusief nieuwe design-tokens volgens NLDS conventies. Opmaak is
  verbeterd voor inhoud met langere linkteksten die naar een nieuwe regel worden afgebroken.
* [:taiga-us:`3509`, :pr:`1997`]: Ondersteuning voor eIDAS login via OIDC is toegevoegd.

Bugfixes
--------

* [:taiga-is:`3518`, :pr:`2000`]: ``maykin-django-prosemirror`` bijgewerkt naar versie
  ``0.3.0``, waardoor het te vroeg laden van de prosemirror JS op bepaalde admin
  pagina's is verholpen.
* [:taiga-is:`3561`, :pr:`1995`]: CMS Categories plugin probeert nu niet meer om zaken
  op te halen wanneer er geen ZGW backend is geconfigureerd.
* [:taiga-is:`3559`, :pr:`1994`]: OpenKlant2 service veld in admin is nu nullable, zodat
  configuraties kunnen worden opgeslagen zonder dat een service is ingesteld.
* [:taiga-is:`2522`:, :pr:`1969`]: Zaken die niet volledig opgehaald kunnen worden uit
  het zaaksysteem worden nu gefilterd uit de zakenlijst om te voorkomen dat de gehele
  lijst van Mijn Zaken toegankelijk blijft.
* [:taiga-is:`3494`: :pr:`1955`]: Verhelpen bug waardoor er sporadisch errors werden
  getoond tijdens het zoeken naar zaken via de algemene zoek-functie.
* [:taiga-is:`3495`: :pr:`1956`]: Bij het aanmaken van contactmomenten onder een zaak
  in OpenKlant2 werd de zaak omschrijving als onderwerp gebruikt. Dit veld is in
  OpenKlant2 echter verplicht, en de omschrijving kan leeg zijn, hetgeen sporadisch tot
  errors leidde. We gebruiken nu de zaak identificatie en een standaard tekst, die
  altijd aanwezig is.
* [:taiga-is:`3486`: :pr:`1946`]: Menu-items op pagina 'Mijn Zaken' worden niet langer
  dubbel getoond in de sidebar en het dropdownmenu.
* [:taiga-is:`3480`, :pr:`1934`]: De paginering van de contactmomenten lijstweergave
  ontbrak, maar is nu toegevoegd.
* [:taiga-is:`3483`,  :pr:`1937`]: Typo's in BRP API request headers verholpen
  (``x-requets-*`` naar ``x-requests-*``).
* [:taiga-is:`3477`: :pr:`1935`]: Wanneer er geen CMS-pagina's zijn en het menu leeg is,
  dan wordt de zijnavigatie nu onzichtbaar, zodat de rest van de inhoud niet meer te smal
  wordt weergegeven.
* [:taiga-is:`3484`]: De pagina voor contactmomenten crashte wanneer het contactformulier
  niet was geconfigureerd.
* [:taiga-is:`3479`: :pr:`1940`]: Ongepubliceerde CMS pagina's worden niet meer
  weergegeven in de zijnavigatie.
* [:taiga-is:`3493`: :pr:`1954`]: Paginering op contactmomenten lijst wordt nu correct
  weergegeven.
* [:taiga-is:`3497`: :pr:`1958`]: Het ophalen van vragen in Openklant geeft geen
  foutmeldingen meer als er ook anonieme vragen voorkomen in de backend.
* [:pr:`1972`]: Informatieobjecttpen die bij de ZGW synchronisatie niet kunnen worden
  opgehaald zullen worden overgeslagen, zodat de overgebleven objecten wel
  gesynchroniseerd kunnen worden.
* [:taiga-is:`3520`, :pr:`1967`]: Missende labels hersteld, die tijdens de migratie voor sommige
  Prosemirror-velden niet waren gekopieerd.
* [:taiga-is:`3519`: :pr:`1966`]: Probleem opgelost in de side menu waarbij de
  'mijn vragen' item niet geselecteerd wordt als huidige pagina.
* [:taiga-is:`3507`: :pr:`1963`]: Verander kleur van menu items bij actieve en hover status
  naar de correcte primaire kleur.
* [:taiga-is:`3525`: :pr:`1978`]: De positie van CMS-pagina's bepaalt niet langer welke
  items worden weergegeven in het verkorte dropdown menu. Menu-items worden nu alleen
  getoond in het dropdown menu als er geen sidenav beschikbaar is en als ze expliciet
  zijn geconfigureerd (op dit moment alleen de link naar "Mijn Profiel").
* [:taiga-is:`3521`, :pr:`1975`]: Probleem opgelost waar de notificatie en mobiele welkom tekst
  overlay op de home pagina in elkaar overlopen.
* [:taiga-is:`3530`: :pr:`1984`]: Uitkeringspagina's tonen nu correct het verkorte
  dropdown menu wanneer er geen sidenav beschikbaar is.
* [:taiga-ta:`3557`, :pr:`1987`]: Ontbrekende verplichte velden toegevoegd aan de
  Subscription detail admin, waardoor het weer mogelijk is om nieuwe Subscription
  objecten aan te maken.
* [:taiga-is:`3507`: :pr:`1993`]: De vaste NLDS-huisstijlkleuren (primaire-, secundaire en accent-
  kleuren) kunnen nu worden overschreven met de kleuren van de colorpicker.
* [:taiga-dimpact:`358`, :pr:`2009`]: Het alternatieve telefoonnummer wordt nu correct verwerkt
  vanuit de eSuite.
* [:taiga-is:`3588`, :pr:`2029`]: Ontbrekende logout URL voor reguliere gebruikers is
  toegoevegd, en de logica voor alle login types is opgeschoond.

Onderhoud
---------

* [:pr:`2024`]: ``brotli`` bijgewerkt naar versie ``1.2.0``.
* [:pr:`1943`]: ``waitress`` bijgewerkt naar versie ``3.0.2``.
* [:pr:`1943`]: ``Flask-CORS`` bijgewerkt naar versie ``6.0.1``.
* [:pr:`1944`]: ``djangorestframework`` bijgewerkt naar versie ``3.16.1``.
* [:taiga-us:`3461`, :taiga-ta:`3472`, :pr:`1834`]: Python versie bijgewerkt naar
  ``v3.12``.
* [:taiga-us:`3450`, :pr:`1927`]: ``maykin-django-prosemirror`` dependency toegevoegd.
* [:taiga-ta:`3473`, :pr:`1931`]: ``maykin-common`` dependency toegevoegd.
* [:pr:`1942`] ``sqlparse`` bijgewerkt naar versie ``0.5.3``.
* [:pr:`1951`] ``django`` bijgewerkt naar versie ``4.2.25``.
* [:pr:`2014`] ``django`` bijgewerkt naar versie ``4.2.26``.
* [:taiga-is:`3496`, :pr:`1957`]: De ``django-setup-configuration`` structuur voor
  configuratie van het klantensysteem is gereorganiseerd om de structuur van het
  beheerscherm te volgen, met een overkoepelend config en sub-configs voor eSuite en
  Openklant.
* [:taiga-ta:`3454`]: ``django-prosemirror`` bijgewerkt naar nieuwste versie
* [:taiga-us:`1514`, :pr:`1976`]: Vertalingen bijgewerkt.
* [:pr:`1974`] De primaire CI testsuite draait op enhanced runner met meer cores,
  en testen voor migrations zijn afgesplitst in een eigen pipeline.
* [:pr:`1977`] Logging is uitgeschakeld in de CI test runs.
* [:pr:`1982`] ``playwright`` (npm) bijgewerkt naar ``>=1.55.1``.
* [:pr:`1980`] Cache decorator ondersteunt kwargs met default argumenten, en maakt
  correct onderscheid tussen ``None`` en ``"None"`` waarden.
* [:pr:`1991`, :taiga-is:`3626`] Vervang het woord "notificaties" met "meldingen"
  omwille van de B1 taaleis.
* [:pr:`2031`] Verouderde ``mozilla-django-oidc-db`` cache-instellingen verwijderd.

1.35.2 (2025-11-13)
===================

Voor een volledig overzicht van alle commits, zie :release:`v1.35.2`.

Onderhoud
---------

* [:pr:`2014`]: ``django`` bijgewerkt naar versie ``4.2.26``.
* [:pr:`2024`]: ``brotli`` bijgewerkt naar versie ``1.2.0``.

Bugfixes
--------

* [:taiga-dimpact:`358`, :pr:`2009`]: Het alternatieve telefoonnummer wordt nu correct
  verwerkt vanuit de eSuite.
* [:taiga-is:`3321`, :pr:`2008`]: Dubbele links in sitemap verwijderd.

1.35.1 (2025-10-29)
===================

Voor een volledig overzicht van alle commits, zie :release:`v1.35.1`.

Bugfixes
--------

* [:taiga-is:`3561`, :pr:`1995`]: CMS Categories plugin probeert nu niet meer om zaken
  op te halen wanneer er geen ZGW backend is geconfigureerd.
* [:taiga-is:`2522`:, :pr:`1969`]: Zaken die niet volledig opgehaald kunnen worden uit
  het zaaksysteem worden nu gefilterd uit de zakenlijst om te voorkomen dat de gehele
  lijst van Mijn Zaken toegankelijk blijft.
* [:taiga-is:`3494`: :pr:`1955`]: Verhelpen bug waardoor er sporadisch errors werden
  getoond tijdens het zoeken naar zaken via de algemene zoek-functie.
* [:taiga-is:`3495`: :pr:`1956`]: Bij het aanmaken van contactmomenten onder een zaak
  in OpenKlant2 werd de zaak omschrijving als onderwerp gebruikt. Dit veld is in
  OpenKlant2 echter verplicht, en de omschrijving kan leeg zijn, hetgeen sporadisch tot
  errors leidde. We gebruiken nu de zaak identificatie en een standaard tekst, die
  altijd aanwezig is.
* [:taiga-is:`3486`: :pr:`1946`]: Menu-items op pagina 'Mijn Zaken' worden niet langer
  dubbel getoond in de sidebar en het dropdownmenu.
* [:taiga-is:`3480`, :pr:`1934`]: De paginering van de contactmomenten lijstweergave
  ontbrak, maar is nu toegevoegd.
* [:taiga-is:`3477`: :pr:`1935`]: Wanneer er geen CMS-pagina's zijn en het menu leeg is,
  dan wordt de zijnavigatie nu onzichtbaar, zodat de rest van de inhoud niet meer te smal
  wordt weergegeven.
* [:taiga-is:`3483`,  :pr:`1937`]: Typo's in BRP API request headers verholpen
  (``x-requets-*`` naar ``x-requests-*``).
* [:taiga-is:`3484`]: De pagina voor contactmomenten crashte wanneer het contactformulier
  niet was geconfigureerd.
* [:taiga-is:`3479`: :pr:`1940`]: Ongepubliceerde CMS pagina's worden niet meer
  weergegeven in de zijnavigatie.
* [:taiga-is:`3493`: :pr:`1954`]: Paginering op contactmomenten lijst wordt nu correct
  weergegeven.
* [:taiga-is:`3497`: :pr:`1958`]: Het ophalen van vragen in Openklant geeft geen
  foutmeldingen meer als er ook anonieme vragen voorkomen in de backend.
* [:taiga-is:`3519`: :pr:`1966`]: Probleem opgelost in de side menu waarbij de
  'mijn vragen' item niet geselecteerd wordt als huidige pagina.
* [:pr:`1972`]: Informatieobjecttpen die bij de ZGW synchronisatie niet kunnen worden
  opgehaald zullen worden overgeslagen, zodat de overgebleven objecten wel
  gesynchroniseerd kunnen worden.
* [:taiga-is:`3525`: :pr:`1978`]: De positie van CMS-pagina's bepaalt niet langer welke
  items worden weergegeven in het verkorte dropdown menu. Menu-items worden nu alleen
  getoond in het dropdown menu als er geen sidenav beschikbaar is en als ze expliciet
  zijn geconfigureerd (op dit moment alleen de link naar "Mijn Profiel").
* [:taiga-is:`3589`, :pr:`2028`]: de omgekeerde migratie voor het toevoegen van
  gedeeltelijke rechten  voor de algemene configuratie geeft geen foutmelding meer
  wanneer er geen rechten bestaan

Onderhoud
---------

* [:pr:`1980`] Cache decorator ondersteunt kwargs met default argumenten, en maakt
  correct onderscheid tussen ``None`` en ``"None"`` waarden.
* [:pr:`1982`] ``playwright`` (npm) bijgewerkt naar ``>=1.55.1``.
* [:taiga-ta:`3557`, :pr:`1987`]: Ontbrekende verplichte velden toegevoegd aan de
  Subscription detail admin, waardoor het weer mogelijk is om nieuwe Subscription
  objecten aan te maken.


1.35.0 (2025-09-18)
===================

Voor een volledig overzicht van alle commits, zie :release:`v1.35.0`.

Deployment aandachtspunten
--------------------------

* Het ``zgw_dev_status`` management commando is verwijderd.
* Het contactformulier is omgezet naar een CMS pagina. Verifieer na deployment de
  beschrijvingen van het contactformulier.

Nieuwe features
---------------

* [:taiga-us:`3370`, :pr:`1888`]: Navigatiemenu-items correct weergegeven op
  verschillende schermbreedtes; ``@gemeente-denhaag/side-navigation`` bijgewerkt naar
  ``4.0.2``, waardoor notificatiebadges in navigatiemenu-items de rode indicator niet
  meer tonen.
* [:taiga-us:`3406`, :pr:`1872`]: Het contactformulier wordt omgezet in een CMS-pagina.
  In plaats van één beschrijving heeft het contactformulier nu twee beschrijvingen, één
  voor geauthenticeerde en één voor anonieme gebruikers. De oude beschrijving wordt naar
  beide nieuwe velden gekopieerd. Pas één of beide beschrijvingen naar behoefte aan.
* [:pr:`1901`, :taiga-ta:`3447`]: ID en abonnement status toegevoegd als alleen-lezen
  velden in de admin detailpagina van de Webhook abonnementen.
* [:taiga-us:`3407`, :pr:`1873`]: De mogelijkheid voor admin gebruikers om een custom
  Javascript bestand te uploaden dat automatisch op alle pagina's van de website wordt
  geladen. Deze functionaliteit wordt gecontroleerd door de ``ALLOW_CUSTOM_JS``
  environment variabele die op deployment niveau moet worden ingesteld.
* [:taiga-us:`3317`, :pr:`1890`]: Er is een nieuwe flag toegevoegd op de ZGW API sets
  (``ZGWApiGroupConfig``) om, bij het opvragen van zaken, gebruik te maken van de
  ``rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__kvkNummer`` en
  ``rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__vestigingsNummer`` query
  parameters, die sinds Open Zaak 1.20 beschikbaar zijn, in plaats van
  ``rol__betrokkeneIdentificatie__vestiging__vestigingsNummer`` en
  ``rol__betrokkeneIdentificatie__nietNatuurlijkPersoon__innNnpId``. Deze flag staat
  standaard uit en moet expliciet aangezet worden voor een specifieke API set in het
  beheerscherm. Zie de documentatie onder "Open Zaak" voor verdere informatie.
* [:taiga-is:`3816`, :pr:`1865`]: Het e-mailverificatiebericht voor nieuwe gebruikers is
  nu configureerbaar.
* [:taiga-us:`2942`, :pr:`1896`, :pr:`1924`]: Er zijn nieuwe rechten toegevoegd waarmee
  gebruikers uitsluitend op specifieke subsets van de Algemene configuratie
  beheer-toegang kunnen ontvangen (kleuren, afbeeldingen, waarschuwingsbanner,
  paginateksten, helpteksten).
* [:taiga-us:`3405`, :pr:`1889`, :pr:`1916`] De documentatie is op verschillende punten
  bijgewerkt en verbeterd.
* [:taiga-us:`3449`, :pr:`1904`]: Verbeterde logmelding voor mislukte API-services
  tijdens updates van gebruikersprofielen

Bugfixes
--------

* [:taiga-is:`3445`, :pr:`1898`]: De sjabloontag field_as_widget ging er onterecht
  vanuit dat het primaire argument een formulierveld was en veroorzaakte daardoor
  sporadisch fouten.
* [:taiga-is:`3459`: :pr:`1908`]: Haal de CMS-pagina voor het contactformulier op basis
  van de sjabloon in plaats van de plug-in (zodat de pagina in de voettekst wordt
  gekoppeld zodra deze is aangemaakt).
* [:taiga-is:`3377`,  :pr:`1917`]: De ``static/bundles/images`` map wordt nu correct
  opgebouwd in de Docker container, waardoor o.m. `marker-icon.png` bestanden correct
  ontsloten worden.
* [:taiga-is:`3466`, :pr:`1922`]: De bitnami images in CI en docker-compose zijn
  vervangen met de officiële Elasticsearch images.
* [:taiga-ta:`3460`, :taiga-us:`3449`, :pr:`1904`]: Het indienen van lege tekstwaarden tijdens
  het bijwerken van het profiel, wat leidde tot fouten in eSuite klant, is opgelost.
* [:pr:`1919`] De docker-compose variabelen voor de Elasticsearch verbinding gebruiken
  nu de verplichte, volledig gekwalificeerde versie van de URL.

Onderhoud
---------

* [:taiga-ta:`3465`, :pr:`1919`] Het Docker start script ondersteunt optioneel het
  kopieren van static files naar een daarvoor aangewezen volume.
* [:cve:`CVE-2024-53899`, :pr:`1892`] ``virtualenv`` bijgewerkt naar versie ``20.34.0``.
* [:pr:`1897`] Het legacy management commando ``zgw_dev_status`` is verwijderd, alsmede
  legacy code voor het beheren van een "default" ZGW API Group.
* [:cve:`CVE-2024-47081`, :cve:`CVE-2024-35195`, :pr:`1905`] ``requests`` bijgewerkt
  naar versie ``2.32.5``.
* [:cve:`CVE-2024-37891`, :cve:`CVE-2024-35195`, :pr:`1905`] ``urllib3`` bijgewerkt naar
  versie ``2.5.0``.
* [:pr:`1905`] ``vcrpy`` bijgewerkt naar versie ``7.0.0``.
* [:pr:`1918`]: ``maykin-2fa`` bijgewerkt naar versie ``1.0.2``.
* [:pr:`1907`, :pr:`1915`, :cve:`CVE-2025-7783`]: ``inline-css`` verwijderd en ``form-data`` override
  bijgewerkt om :cve:`CVE-2025-7783` te mitigeren.

1.34.2 (2025-10-07)
===================

Voor een volledig overzicht van alle commits, zie :release:`v1.34.2`.

Bugfixes
--------
* [:taiga-is:`3493`: :pr:`1954`]: Paginering op contactmomenten lijst wordt nu correct
  weergegeven.

1.34.1 (2025-10-02)
===================

Voor een volledig overzicht van alle commits, zie :release:`v1.34.1`.

Bugfixes
--------

* [:taiga-is:`3377`,  :pr:`1917`]: De ``static/bundles/images`` map wordt nu correct
  opgebouwd in de Docker container, waardoor o.m. `marker-icon.png` bestanden correct
  ontsloten worden.
* [:taiga-is:`3480`, :pr:`1934`]: De paginering van de contactmomenten lijstweergave
  ontbrak, maar is nu toegevoegd.
* [:taiga-is:`3483`,  :pr:`1937`]: Typo's in BRP API request headers verholpen
  (``x-requets-*`` naar ``x-requests-*``).
* [:taiga-is:`3477`: :pr:`1935`]: Wanneer er geen CMS-pagina's zijn en het menu leeg is,
  dan wordt de zijnavigatie nu onzichtbaar, zodat de rest van de inhoud niet meer te smal
  wordt weergegeven.
* [:taiga-is:`3479`: :pr:`1940`]: Ongepubliceerde CMS pagina's worden niet meer
  weergegeven in de zijnavigatie.
* [:taiga-is:`3486`: :pr:`1946`]: Menu-items op pagina 'Mijn Zaken' worden niet langer
  dubbel getoond in de sidebar en het dropdownmenu.
* [:taiga-is:`3445`, :pr:`1898`]: De sjabloontag field_as_widget ging er onterecht
  vanuit dat het primaire argument een formulierveld was en veroorzaakte daardoor
  sporadisch fouten.
* [:taiga-is:`3466`, :pr:`1922`]: De bitnami images in CI en docker-compose zijn
  vervangen met de officiële Elasticsearch images.
* [:taiga-ta:`3460`, :taiga-us:`3449`, :pr:`1904`]: Het indienen van lege tekstwaarden
  tijdens het bijwerken van het profiel, wat leidde tot fouten in eSuite klant, is
  opgelost.

Onderhoud
---------

* [:pr:`1907`, :pr:`1915`, :cve:`CVE-2025-7783`]: ``inline-css`` verwijderd en ``form-data`` override
  bijgewerkt om :cve:`CVE-2025-7783` te mitigeren.
* [:taiga-is:`3466`, :pr:`1922`]: De bitnami images in CI en docker-compose zijn
  vervangen met de officiële Elasticsearch images.
* [:pr:`1951`] ``django`` bijgewerkt naar versie ``4.2.25``.

1.34.0 (2025-09-03)
===================

Voor een volledig overzicht van alle commits, zie :release:`v1.34.0`.

Nieuwe features
---------------

* [:taiga-us:`3368`, :pr:`1839`]: Een anoniem ingevuld contactformulier wordt nu ook in
  de OpenKlant2 backend opgeslagen.
* [:taiga-us:`3370`, :pr:`1837`, :pr:`1869`]: Het navigatiemenu is nu conform het NL
  Design System op de meeste pagina's aan de linkerkant van het scherm geplaatst.
  Sommige detailpagina's behouden voorlopig het dropdownmenu in afwachting van nieuwe
  designs.

Bugfixes
--------

* [:taiga-is:`3396`, :taiga-is:`3395`, :pr:`1852`, :pr:`1853`]: Verschillende problemen
  bij het ophalen van contactmomenten uit OpenKlant2 zijn opgelost.
* [:taiga-is:`3389`, :pr:`1845`]: De synchronisatie van gebruikersprofielen met
  OpenKlant gebeurt nu ook direct na registratie, niet alleen na inloggen.
* [:taiga-is:`3375`, :pr:`1868`]: Correct afbreken van lange woorden en e-mailadressen
  in smalle tegels, zoals bij productlocaties.
* [:taiga-dimpact:`297`, :pr:`1866`]: Het verwijderen van websites en het toevoegen van
  sites naast de primaire website wordt voorkomen.

Onderhoud
---------

* [:taiga-us:`3393`, :pr:`1871`]: Kleine tekstuele verbeteringen zijn doorgevoerd om de
  teksten B1-conform te maken.
* [:pr:`1878`]: Aanpassen pipeline for het bijhouden en publiceren van de changelog op
  de documentatie pagina.
* [:pr:`1884`]: ``django-setup-configuration`` bijgewerkt naar versie ``0.9.0``. Hiermee
  ondersteunt Open Inwoner het verwijzen naar environment variables in de setup
  configuration YAML bestanden.
* [:pr:`1886`, :cve:`CVE-2025-57833`]: ``django`` bijgewerkt naar versie ``4.2.24``,
  waarmee een `beveiligingsissue met severity "high"
  <https://www.djangoproject.com/weblog/2025/sep/03/security-releases/>`_ wordt
  opgelost.
