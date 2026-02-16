2.2.0-dev (2026-XX-XX)
======================

Voor een volledig overzicht van alle commits, zie ...

Deployment aandachtspunten
--------------------------

* ...

Nieuwe features
---------------

* ...

Bugfixes
--------

* [:gh:`2329`]: ``attr_consuming_service_index`` wordt nu correct doorgegeven als
  queryparameter aan de eHerkenning SAML loginpagina, op basis van de waarde in de
  eHerkenning configuratie. Het ontbreken hiervan kon leiden tot authenticatiefouten.
* [:gh:`2326`]: Correctie van Nederlandse vertalingen voor 'verwerking' header in
  Haalcentraal BRP configuratie (was onjuist vertaald als 'doelbinding').
* [:gh:`2323`]: Correctie van Centric BRP HTTP header namen voor iConnect integratie
  (gebruik van 'x-request-*' in plaats van 'x-requests-*').
* [:gh:`2290`]: Correctie van cache key voor ``fetch_zaak_roles`` om
  ``betrokkene_type`` parameter op te nemen, waardoor verkeerde cache hits worden
  voorkomen.
* [:gh:`2294`]: Aangepaste Sentry processor voor structlog geïmplementeerd om uitzonderingen
  efficiënter te loggen. De processor voorkomt database-toegang en serialisatie-fouten tijdens
  foutafhandeling door niet-primitieve types om te zetten naar veilige placeholders. Bevat
  recursie-bescherming en uitgebreide tests.
* [:gh:`2278`]: Correctie in de sortering zaken. Alle zaken worden nu gesorteerd op startdatum.
* [:gh:`2309`]: Uitlijning melding "Registratie voltooid" zonder banner afbeelding opgelost.
* [:gh:`2307`] Correctie van ProseMirror velden in zaakstatus templates om HTML correct
  weer te geven. ``status.description`` en ``document_upload_description`` gebruiken nu
  het ``prosemirror_content`` filter in plaats van direct de ``.html`` property of
  zonder filter, zodat opmaak (vet, cursief, links) correct wordt gerenderd.

Onderhoud
---------

* [:gh:`2283`]: De grafiek en filters op de Mijn Afval pagina zijn niet meer zichtbaar wanneer er geen data beschikbaar is.
* [:gh:`2303`, :cve:`CVE-2026-29074`, :cve:`CVE-2026-29063`]: ``cssnano`` bijgewerkt om :cve:`CVE-2026-29074` te mitigeren en
  ``immutable`` override bijgewerkt om :cve:`CVE-2026-29063` te mitigeren.
* [:gh:`2314`, :cve:`CVE-2026-32597`]: ``PyJWT`` bijgewerkt naar versie ``2.10.1`` om
  kwetsbaarheid in ``crit`` header te mitigeren.
* [:gh:`2295`]: Zaken-kaartjes op de homepage gebruiken nu het ``arrow_forward`` icoon en hebben een gelijke hoogte.
* [:gh:`2318`]: ``vitest`` en ``@vitest/ui`` bijgewerkt naar versie ``4.1.0``.

2.1.0 (2026-03-04)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.1.0`.

Deployment aandachtspunten
--------------------------

* [:gh:`2156`]: De omgevingsvariabele ``OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS`` is nu
  beschikbaar om de sessie-vernieuwingsinterval voor OpenID Connect (DigiD/eHerkenning)
  te configureren. De standaardwaarde is ``900`` seconden (15 minuten). Zie hoofdstuk 10
  van de beheerhandleiding voor meer informatie.
* [:gh:`2130`]: Er zijn nu gestandardiseerde HTTP healthchecks beschikbaar voor gebruik
  in Docker/Kubernetes. Zie de `documentatie over health checks
  <https://docs.openinwoner.nl/en/v2.1.0/installation/health_checks.html>`_.

Nieuwe features
---------------

* [:taiga-us:`3607`, :pr:`2075`, :pr:`2079`, :pr:`2193`]: Basisapp ‘Mijn Afval’ geïmplementeerd en
  geïntegreerd met Django CMS.
* [:gh:`2101`, :oip-nlds:`30`, :oip-nlds:`34`]: Styling van tegels op de Home pagina en van externe-links plugin
  op de Home pagina overgezet naar design-tokens zodat deze volgens de NLDS principes gebruikt kunnen worden.
* [:gh:`2098`, :gh:`2177`]: Nieuw accordion web component toegevoegd dat gebruikt wordt in Mijn
  Afval.
* [:gh:`2096`, :oip-nlds:`32`]: Table component toegevoegd ten behoeve van de ‘Mijn
  Afval’ app inclusief NL Design-System design-tokens.
* [:gh:`2099`] De OIP Storybook is nu beschikbaar via GitHub pages.
* [:gh:`2130`]: Er zijn nu gestandardiseerde HTTP healthchecks beschikbaar voor gebruik
  in Docker/Kubernetes.
* [:gh:`2113`]: Diagram (chart.js) toegevoegd ten behoeve van de 'Mijn Afval' app.
* [:gh:`2119`, :gh:`2182`, :pr:`2151`]: API-client en configuratie voor 'Mijn Afval' aangemaakt.
* [:gh:`2157`, :gh:`2205`]: Toon het nieuwste antwoord op OpenKlant-vragen.
* [:gh:`2192`, :pr:`2195`]: Filters voor 'Mijn Afval' geïmplementeerd.
* [:gh:`2220`]: De eerste versie van het NL design-system File component, waarmee een bestand getoond kan worden,
  is toegevoegd aan de Samenwerkingen detailpagina.
* [:gh:`2192`, :pr:`2195`, :pr:`2200`]: Filters voor 'Mijn Afval' geïmplementeerd.
* [:gh:`2156`]: Omgevingsvariabele ``OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS`` toegevoegd om
  de sessie-vernieuwingsinterval voor OpenID Connect (DigiD/eHerkenning) te
  configureren. OIDC-foutmeldingen vereenvoudigd om alleen op foutcode te matchen.
  Nederlandse foutmeldingen voor DigiD en eHerkenning verbeterd.
* [:gh:`2247`]: Documentatie toegevoegd voor het configureren van de Takenlijst CMS
  plugin in de beheerhandleiding. Pydantic modellen voor externe taken herzien om
  field conflicts op te lossen: record data (``ExternFormulierTaakRecord``,
  ``UrlTaakRecord``) gescheiden van Objects API envelope models
  (``ExternFormulierTaakObject``, ``UrlTaakObject``).
* [:gh:`2255`]: Titels en tabellen toegevoegd aan de product-veelgestelde-vragen tekstopties.
* [:gh:`2280`]: Verbeteringen doorgevoerd aan de Mijn Taken-plugin op de homepagina. De titel heeft extra spacing
  gekregen, kaartjes openen nu in een nieuw tabblad en de aanduiding ‘Soort:’ is verwijderd.
* [:gh:`2254`] Shift+Enter voegt nu een hard break (br) toe in alle ProseMirror-velden.

Bugfixes
--------

* [:gh:`2091`]: Beheerders toestaan om uit te loggen via frontend.
* [:gh:`2131`]: Probleem met ``vite`` bundler opgelost waardoor de marker van de kaart
  weer correct wordt geladen.
* [:gh:`2125`]: ``django-digid-eherkenning`` bijgewerkt naar custom release zodat de
  juiste DigiD SAML Foutmeldingen worden gebruikt.
* [:gh:`2191`]: Foutmelding opgelost in Afval Profiel pagina waar `messages.error()` en `messages.info()`
  zonder verplicht `request` argument werden aangeroepn.
* [:gh:`2209`, :pr:`2213`]: Ckeditor opnieuw toegevoegd aan INSTALLED_APPS voor compatibiliteit met
  mail-editor.
* [:gh:`2214`]: Datamigratie toegevoegd die oude ``djangocms_text_ckeditor_text`` tabel
  opruimt door CKEditor TextPlugin instanties te migreren naar het nieuwe Prosemirror
  formaat. HTML content wordt geconverteerd naar Prosemirror's JSON structuur, met
  fallback strategieën voor ongeldige HTML. Na succesvolle migratie wordt de oude
  tabel verwijderd.
* [:gh:`2208`]: Link plugin rendert nu correct HTML uit ProsemirrorModelField in plaats van
  markup als tekst weer te geven.
* [:gh:`2210`]: Exports en imports van de ZGW catalogi via bestanden gaat nu correct om
  met prosemirror velden. Tevens zullen via een datamigratie de bestaande velden in de
  ZGW catalogus gechecked worden op valide waarden voor de prosemirror velden.
* [:gh:`2212`]: ``referrerpolicy="strict-origin-when-cross-origin"`` toegevoegd aan de video
  iframe om het site-brede referrerbeleid te overschrijven voor dit specifieke element.
* [:gh:`2256`]: Probleem opgelost waarbij externe link-iconen bij product-veelgestelde vragen ontbraken.
* [:gh:`2263`]: Het woord 'E-mailmeldingen' is onterecht met een hoofdletter is geschreven in de
  zaakmeldingen optie.

Onderhoud
---------

* [:taiga-us:`3615`]: zgw-klassen, methoden en variabelen hernoemd om Nederlandse termen
  te gebruiken
* [:gh:`2126`, :cve:`CVE-2026-27148`]: ``storybook`` en storybook plugins bijgewerkt naar versie ``10.2.14``.
* [:gh:`2112`] ``README.rst`` bijgewerkt met Storybook link en correctie in badges en
  copyright.
* [:gh:`2104`]: Verwijderen in ongebruik geraakte NPM dependencies, ``jest`` en ``karma``
  test suite en configuratie (``karma.conf.js``) en configuratie bestanden (``stylelint.rc``,
  ``.babelrc`` en ``.jshintrc``).
* [:gh:`2166`]:  ``weasyprint`` bijgewerkt naar versie ``0.68``.
* [:gh:`2179`, :cve:`CVE-2025-13465`]: ``@utrecht/component-library-react`` bijgewerkt naar versie ``13.0.0``.
* [:gh:`2198`, :pr:`2197`]: Django bijgewerkt naar versie ``4.2.28``.
* Django bijgewerkt naar versie ``4.2.29``.
* [:gh:`2206`, :pr:`2207`]: `setuptools` bijgewerkt naar versie ``<81``.
* [:gh:`2178`, :cve:`CVE-2023-44270`]: ``autoprefixer`` bijgewerkt naar versie ``10.4.23``.
* [:gh:`2181`]: Alle (huidige) postcss waarschuwingen opgelost.
* [:pr:`2226`]: Verwijderde dubbele vermeldingen uit changelog.
* [:gh:`2228`]: ``vite`` configuratie verbeterd.
* [:gh:`2232`]: Bijgewerkte admin index-fixture.
* [:gh:`2082`]: Elasticsearch-verbindingscache gewist in tests.
* [:gh:`2251`, :cve:`CVE-2026-27606`]: ``rollup`` bijgewerkt naar versie ``^4.59.0``.
* ``urllib3`` bijgewerkt naar versie ``2.6.3``.
* ``protobuf`` bijgewerkt naar versie ``6.33.5``.
* ``sqlparse`` bijgewerkt naar versie ``0.5.5``.

2.0.3 (2026-02-20)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.0.3`.

Bugfixes
--------

* [:gh:`2206`]: ``setuptools`` versie vastgezet op <81 om ``pkg_resources`` beschikbaar te
  houden voor legacy dependencies (``django-axes``, ``django-formtools``).
* [:gh:`2214`]: Datamigratie toegevoegd die oude ``djangocms_text_ckeditor_text`` tabel
  opruimt door CKEditor TextPlugin instanties te migreren naar het nieuwe Prosemirror
  formaat. HTML content wordt geconverteerd naar Prosemirror's JSON structuur, met
  fallback strategieën voor ongeldige HTML. Na succesvolle migratie wordt de oude
  tabel verwijderd.
* [:gh:`2208`]: Link plugin rendert nu correct HTML uit ProsemirrorModelField in plaats van
  markup als tekst weer te geven.
* [:gh:`2210`]: Exports en imports van de ZGW catalogi via bestanden gaat nu correct om
  met prosemirror velden. Tevens zullen via een datamigratie de bestaande velden in de
  ZGW catalogus gechecked worden op valide waarden voor de prosemirror velden.
* [:gh:`2209`, :pr:`2213`]: Ckeditor opnieuw toegevoegd aan INSTALLED_APPS voor
  compatibiliteit met mail-editor.

2.0.2 (2026-01-27)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.0.2`.

Bugfixes
--------

* [:gh:`2166`]: ``weasyprint`` bijgewerkt naar versie ``0.68``.

2.0.1 (2026-01-26)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.0.1`.

Bugfixes
--------

* [:gh:`2116`]: Naamgeving conflict tussen Prosemirror en Leaflet opgelost,
  waardoor de Prosemirror editor op alle pagina's naar verwachting werkt.
* [:gh:`2107`]: Productie logs worden weggeschreven als JSON voor
  gebruik in log analyse tools.
* [:gh:`2158`]: PDC product content editor mag nu ook lijsten gebruiken.
* [:gh:`2164`, :cve:`CVE-2026-22028`] ``preact`` bijgewerkt naar versie
  ``10.27.3``.

2.0.0 (2026-01-05)
==================

Voor een volledig overzicht van alle commits, zie :release:`v2.0.0`.

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
* Zaaktype Configuraties die in eerdere versies zijn geëxporteerd, kunnen niet worden
  geïmporteerd in versie ``2.0.0`` vanwege wijzigingen in het database formaat. Upgrade
  eerst uw bronomgeving naar ``2.0.0`` zodat bron en bestemming hetzelfde formaat hanteren.
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
* Het aantal requests aan zaken API's is nu configureerbaar via een omgevingsvariabele ``ZGW_MAX_REQUESTS``
  (standaardwaarde is 8).
* De nieuwe omgevingsvariabele ``OIDC_FRONTEND_LOGOUT_WITH_HINTS`` (standaard: ``true``)
  bepaalt of hints zoals ``id_token_hint`` en ``post_logout_redirect_uri`` worden
  meegegeven bij OIDC frontend logout redirects. Wanneer het ID token gevoelige claims
  bevat die niet in de querystring van de user agent mogen verschijnen (bijvoorbeeld
  voor security compliance), kan deze variabele op ``false`` worden gezet om alleen naar
  het logout endpoint te redirecten zonder aanvullende parameters.
* Wanneer via de color-picker of in CSS een secundaire kleur wordt ingesteld die anders is dan
  de primaire kleur (CSS-variabelen ``--color-primary`` en ``--color-secondary``) is hier nu een
  stijl verandering te zien. Call-to-action elementen gebruiken nu altijd de primaire kleur. Hierdoor
  worden de knoppen in tegels niet langer in een afwijkende secundaire kleur weergegeven.
* Hou er rekening mee dat de nieuwe frontend web-componenten mogelijk niet meteen
  correct worden weergegeven bij het initieel laden van de pagina. Zorg dat u in dat
  geval een zogenaamde "hard refresh" doet om er zeker van te zijn dat de frontend
  javascript en CSS bestanden opnieuw worden geladen (in meeste browsers is dit de
  toetsencombinatie Shift/CTRL + F5).

Nieuwe features
---------------

* [:taiga-us:`3478`, :pr:`1953`, :pr:`2089`]: Extra OpenTelemetry metrics toegevoegd voor
  account- en profiel gerelateerde acties, zoals aanmeldingen, registraties,
  uitnodigingen en profielwijzigingen.
* [:taiga-us:`3461`, :taiga-ta:`3473`, :pr:`1932`]: Basisinfrastructuur voor
  OpenTelemetry toegevoegd, inclusief logging en metrics ondersteuning voor
  observability.
* [:taiga-us:`3408`, :pr:`1881`]: Nieuw selectiescherm voor eHerkenning-inlog met zoek-
  en dropdownfunctie voor betere UX waarmee gewiseld kan worden tussen vestigingen.
* [:taiga-us:`3450`, :taiga-ta:`3454`, :pr:`2067`]: CKEditor wordt vervangen door Prosemirror
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
* [:taiga-us:`3575`, :pr:`2020`, :pr:`2037`, :pr:`2042`, :pr:`2058`]: CMS plug-in 'Mijn Zaken' aangemaakt voor het
  ontsluiten van zaken in de startpagina.
* [:taiga-us:`3574`, :pr:`2026`]: Aantal requests aan zaken API's configureerbaar gemaakt via
  omgevingsvariabele.
* [:taiga-us:`3576`, :pr:`2034`]: Front-end voor CMS plug-in 'Mijn Zaken' gebouwd met design-tokens
  volgens het NLDS principe.
* [:taiga-us:`3596`, :pr:`2036`]: Hints (zoals ``id_token_hint`` en
  ``post_logout_redirect_uri``) bij OIDC frontend logout zijn nu optioneel
  configureerbaar via de omgevingsvariabele ``OIDC_FRONTEND_LOGOUT_WITH_HINTS``. Dit
  voorkomt dat gevoelige claims in de querystring van de user agent terechtkomen, wat
  belangrijk kan zijn voor security audits (zoals PENTests) van bijvoorbeeld DigiD.
  Standaard blijven de hints ingeschakeld om het huidige gedrag te behouden.
* [:taiga-us:`3580`, :pr:`2033`]: De zoekfunctie kan nu worden uitgeschakeld in de Algemene Configuratie.
* [:taiga-is:`3600`, :pr:`2046`]: 'Signing requests' toegevoegd aan admin. Beheerders kunnen nu een CSR
  (Certificate Signing Request) genereren in de admin via 'Datakoppelingen > Ondertekeningsverzoeken'.
* [:taiga-us:`3579`, :pr:`2049`, :pr:`2056`, :pr:`2064`]: Het commando om de ZGW Catalogus te importeren geeft
  nu uitgebreidere informatie (bijvoorbeeld welke zaaktypes wel zijn ontvangen maar niet
  gesynchroniseerd vanwege een geconfigureerd filter), en zorgt ervoor dat alle velden
  uit de API correct worden overgenomen in de lokale versie van de catalogus. ZGW objecten
  die niet meer in de API gevonden worden, worden nu gemarkeerd met een ``found_in_api``
  vlag zodat verweesde configuratie makkelijk kan worden geïdentificeerd.
* [:taiga-us:`3578`, :pr:`2043`]: Nieuw Front-end ontwerp voor CMS plug-in 'Balie Afspraken' gebouwd met
  design-tokens volgens het NLDS principe.
* [:taiga-us:`3615`, :pr:`2051`, :pr:`2065`]: Zaken en open formulieren hebben nu
  verschillende teksten voor de status en actieknop/link en op de Home pagina. Het
  zaaknummer wordt alleen getoond voor reguliere zaken, niet voor formulieren.
* [:taiga-us:`3606`]: Experimentele client geïmplementeerd met mock data ter ondersteuning van het ontwikkelen
  van de 'Mijn Afval' module.
* [:pr:`1983`]: Optie toegevoegd om zaken rollen te filteren op type betrokkene
  (‘natuurlijke persoon’, ‘niet-natuurlijke persoon’, ‘vestiging’).

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
* [:taiga-is:`3471`: :pr:`2007`]: De paginatitel van de sitemap verandert nu mee met de in de
  configuratie meegegeven site-naam.
* [:taiga-dimpact:`358`, :pr:`2009`]: Het alternatieve telefoonnummer wordt nu correct verwerkt
  vanuit de eSuite.
* [:taiga-is:`3590`: :pr:`2030`]: Bug opgelost waarbij tablet gebruikers geen volledig uitgevuld
  navigatie menu zagen.
* [:taiga-is:`3572`: :pr:`2019`]: De kleuren van call-to-action links en knoppen in tegels komen
  nu overeen met de primaire kleur zoals die in de Figma designs vastgelegd is.
* [:taiga-is:`3588`, :pr:`2029`]: Ontbrekende logout URL voor reguliere gebruikers is
  toegoevegd, en de logica voor alle login types is opgeschoond.
* [:taiga-is:`3599`, :pr:`2045`]: Bij het bekijken van de bron code van componenten in Storybook
  wordt nu de correcte styling getoond.
* [:taiga-ta:`3636`, :pr:`2068`]: Automatisch toegevoegen van een extra veelgestelde vraag in
  product admin is uitgezet.
* [:taiga-is:`3537`, :taiga-is:`3321`, :pr:`2061`]: Sitemap bijgewerkt: duplicaten verwijderd,
  structuur vereenvoudigd.

Onderhoud
---------

* [:pr:`2044`]: ``django-simple-certmanager`` bijgewerkt naar versie ``2.5.0``.
* [:pr:`2039`]: ``locust`` bijgewerkt naar versie ``2.39.1``.
* [:pr:`2039`]: ``jinja2`` bijgewerkt naar versie ``3.1.6``.
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
* [:pr:`2048`] ``django`` bijgewerkt naar versie ``4.2.27``.
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
* [:pr:`2041`]: ``certifi`` bijgewerkt naar versie ``2025.11.12``.
* [:taiga-us:`3581`, :pr:`2050`]: Vertalingen bijgewerkt.
* [:pr:`2018`, :pr:`2063`] ``objects-api-client-django`` bijgewerkt naar nieuwste
  versie ``0.5.0``.
* [:pr:`2057`]: ``node`` bijgewerkt naar versie ``24.12`` en ``node:20-bookworm-slim``
  bijgewerkt naar ``node:24-bookworm-slim`` in Docker container.
* [:pr:`2070`]: ``fonttools`` bijgewerkt naar versie ``4.46.1``, ``cryptography``
  bijgewerkt naar ``45.0.7``, ``webob`` bijgewerkt naar ``1.8.9``, en ``urllib3``
  bijgewerkt naar ``2.6.2``.
* [:pr:`2087`]: ``cbor2`` bijgewerkt naar versie ``5.8.0``.
* [:pr:`2054`]: ``webpack`` volledig vervangen met ``vite``.

1.35.3 (2025-11-24)
===================

Voor een volledig overzicht van alle commits, zie :release:`v1.35.3`.

Deployment aandachtspunten
--------------------------

* De nieuwe omgevingsvariabele ``OIDC_FRONTEND_LOGOUT_WITH_HINTS`` (standaard: ``true``)
  bepaalt of hints zoals ``id_token_hint`` en ``post_logout_redirect_uri`` worden
  meegegeven bij OIDC frontend logout redirects. Wanneer het ID token gevoelige claims
  bevat die niet in de querystring van de user agent mogen verschijnen (bijvoorbeeld
  voor security compliance), kan deze variabele op ``false`` worden gezet om alleen naar
  het logout endpoint te redirecten zonder aanvullende parameters.


Nieuwe features
---------------

* [:taiga-us:`3596`, :pr:`2036`]: Hints (zoals ``id_token_hint`` en
  ``post_logout_redirect_uri``) bij OIDC frontend logout zijn nu optioneel
  configureerbaar via de omgevingsvariabele ``OIDC_FRONTEND_LOGOUT_WITH_HINTS``. Dit
  voorkomt dat gevoelige claims in de querystring van de user agent terechtkomen, wat
  belangrijk kan zijn voor security audits (zoals PENTests) van bijvoorbeeld DigiD.
  Standaard blijven de hints ingeschakeld om het huidige gedrag te behouden.

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
