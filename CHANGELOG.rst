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
