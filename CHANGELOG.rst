1.35.0 (2025-XX-YY) [UNRELEASED]
================================

Voor een volledig overzicht van alle commits, zie ...

Nieuwe features
---------------

* [:taiga-us:`3370`, :pr:`1888`]: Navigatiemenu-items correct weergegeven op verschillende schermbreedtes; 
  ``@gemeente-denhaag/side-navigation`` bijgewerkt naar ``4.0.2``, waardoor notificatiebadges in 
  navigatiemenu-items de rode indicator niet meer tonen.
* [:taiga-us: `3406`, :pr:`1872`]: Het contactformulier wordt omgezet in een CMS-pagina.
  In plaats van één beschrijving heeft het contactformulier nu twee beschrijvingen, één voor
  geauthenticeerde en één voor anonieme gebruikers. De oude beschrijving wordt naar beide
  nieuwe velden gekopieerd. Pas één of beide beschrijvingen naar behoefte aan.

Bugfixes
--------

* ...

Onderhoud
---------

* [:cve:`CVE-2024-53899`, :pr:`1892`] ``virtualenv`` bijgewerkt naar versie ``20.34.0``.

Deployment aandachtspunten
--------------------------

* Het contactformulier is omgezet naar een CMS pagina. Verifieer na deployment de beschrijvingen van het
  contactformulier.

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
* [:pr:`1886`, :cve:`CVE-2025-57833`]: ``django`` bijgewerkt naar versie ``4.2.24``,
  waarmee een `beveiligingsissue met severity "high"
  <https://www.djangoproject.com/weblog/2025/sep/03/security-releases/>`_ wordt
  opgelost.
