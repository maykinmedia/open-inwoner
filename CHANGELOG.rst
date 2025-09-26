1.36.0 (2025-09-18) [UNRELEASED]
================================

Voor een volledig overzicht van alle commits, zie ...

Deployment aandachtspunten
--------------------------

* ...

Nieuwe features
---------------

* ...

Bugfixes
--------

* [:taiga-is:`3480`, :pr:`1934`]: De paginering van de contactmomenten lijstweergave
  ontbrak, maar is nu toegevoegd.
* [:taiga-is:`3483`,  :pr:`1937`]: Typo's in BRP API request headers verholpen
  (``x-requets-*`` naar ``x-requests-*``).
* [:taiga-is:`3477`: :pr:`1935`]: Wanneer er geen CMS-pagina's zijn en het menu leeg is,
  dan wordt de zijnavigatie nu onzichtbaar, zodat de rest van de inhoud niet meer te smal
  wordt weergegeven.

Onderhoud
---------

* [:pr:`1943`]: ``waitress`` bijgewerkt naar versie ``3.0.2``.
* [:pr:`1943`]: ``Flask-CORS`` bijgewerkt naar versie ``6.0.1``.
* [:pr:`1944`]: ``djangorestframework`` bijgewerkt naar versie ``3.16.1``.
* [:taiga-us:`3461`, :taiga-ta:`3472`, :pr:`1834`]: Python versie bijgewerkt naar
  ``v3.12``.
* [:taiga-us:`3450`, :pr:`1927`]: ``maykin-django-prosemirror`` dependency toegevoegd.
* [:taiga-ta:`3473`, :pr:`1931`]: ``maykin-common`` dependency toegevoegd.
* [:pr:`1942`] ``sqlparse`` bijgewerkt naar versie ``0.5.3``.

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
