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

* [:taiga-us:`3368`, :pr:`1839`]: Een anoniem ingevuld contactformulier wordt nu ook in de
  OpenKlant2 backend opgeslagen.
* [:taiga-us:`3370`, :pr:`1837`, :pr:`1869`]: Het navigatiemenu is nu conform het NL Design
  System op de meeste pagina's aan de linkerkant van het scherm geplaatst. Sommige
  detailpagina's behouden voorlopig het dropdownmenu in afwachting van nieuwe designs.

Bugfixes
--------

* [:taiga-is:`3396`, :taiga-is:`3395`, :pr:`1852`, :pr:`1853`]: Verschillende problemen
  bij het ophalen van contactmomenten uit OpenKlant2 zijn opgelost.
* [:taiga-is:`3389`, :pr:`1845`]: De synchronisatie van gebruikersprofielen met
  OpenKlant gebeurt nu ook direct na registratie, niet alleen na inloggen.
* [:taiga-is:`3375`, :pr:`1852`, :pr:`1868` ]: Correct afbreken van lange woorden en
  e-mailadressen in smalle tegels, zoals bij productlocaties.
* [:taiga-dimpact:`297`, :pr:`1866`]: Het verwijderen van websites en het toevoegen van
  sites naast de primaire website wordt voorkomen.

Onderhoud
---------

* [:taiga-us:`3393`, :pr:`1871`]: Kleine tekstuele verbeteringen zijn doorgevoerd om de
  teksten B1-conform te maken.
* [:pr:`1878`]: Aanpassen pipeline for het bijhouden en publiceren van de changelog
  op de documentatie pagina.
* [:pr:`1884`]: ``django-setup-configuration`` bijgewerkt naar versie ``0.9.0``.
  Hiermee ondersteunt Open Inwoner het verwijzen naar environment variables in de
  setup configuration YAML bestanden.
* [:pr:`1886`]: ``django`` bijgewerkt naar versie ``4.2.24``, waarmee een
  `beveiligingsissue met severity "high"
  <https://www.djangoproject.com/weblog/2025/sep/03/security-releases/>`_ wordt
  opgelost.
