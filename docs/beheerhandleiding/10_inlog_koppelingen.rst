.. _inlog_koppelingen:

=====================
10. Inlog koppelingen
=====================

Bij inlog koppelingen kunt u de authenticatiemogelijkheden voor inwoners, bedrijven en beheerders instellen.

10.1. Configuratie ‘Haal centraal’
==================================

Dit dient ter configuratie van de BRP-integratie met de Open Inwoner omgeving. De beheerder stelt hier de Haal Centraal API-service en BRP-versie in, en configureert de HTTP-headers die met elke aanvraag worden meegestuurd.

**BRP versie**

Selecteer de versie van de Haal Centraal BRP API die uw leverancier ondersteunt:

- ``1.3`` — BRP 1.3 (GET-gebaseerde API, endpoint ``ingeschrevenpersonen``)
- ``2.0`` t/m ``2.7`` — BRP 2.x (POST-gebaseerde API, endpoint ``personen``)

.. note::

   Patch versies hebben geen invloed op de keuze: gebruikt uw leverancier bijvoorbeeld
   versie 2.6.2, kies dan ``2.6``.

**Request headers**

Voer de HTTP-headers in als sleutel/waarde-paren die bij elke BRP-aanvraag worden toegevoegd. Welke headers vereist zijn is afhankelijk van uw leverancier:

*I Connect*

+--------------------+------------------------------------------+
| Header             | Omschrijving                             |
+====================+==========================================+
| x-origin-oin       | OIN van de gemeente (afzender)           |
+--------------------+------------------------------------------+
| x-afnemer-oin      | OIN van de afnemer                       |
+--------------------+------------------------------------------+
| x-doelbinding      | Doelbinding van de aanvraag              |
+--------------------+------------------------------------------+
| x-verwerking       | Verwerkingsactiviteit (vrij tekstveld)   |
+--------------------+------------------------------------------+

*Centric*

+--------------------------+------------------------------------------+
| Header                   | Omschrijving                             |
+==========================+==========================================+
| x-request-organization   | Organisatienaam                          |
+--------------------------+------------------------------------------+
| x-request-application    | Applicatienaam                           |
+--------------------------+------------------------------------------+
| x-request-afnemerscode   | Afnemerscode                             |
+--------------------------+------------------------------------------+
| x-request-user           | Gebruikersnaam                           |
+--------------------------+------------------------------------------+

Raadpleeg de documentatie van uw leverancier voor de exacte waarden.

.. note::

   De waarde van ``x-verwerking`` werd in eerdere versies gevalideerd op het voorkomen van maximaal één ``@``-teken. Deze validatie is vervallen omdat het veld is vervangen door een generiek sleutel/waarde-veld zonder leverancierspecifieke beperkingen.

10.2. DigiD configuratie
========================

Dit is de configuratie voor de koppeling van het Open Inwoner platform met DigiD van Logius. Bij de onboarding van Open Inwoner wordt bij deze configuratie hulp geboden.

.. note::

   Wanneer de OpenID Connect-koppeling voor DigiD is ingeschakeld (zie sectie 10.5),
   vervangt deze de SAML-koppeling op de loginpagina. Beide kunnen niet tegelijkertijd
   actief zijn.

10.3. eHerkenning/eIDAS configuratie
====================================

Dit is de configuratie voor de koppeling van het Open Inwoner platform met eHerkenning bij een eHerkenningsmakelaar. Bij de onboarding van Open Inwoner wordt bij deze configuratie hulp geboden.

.. note::

   Wanneer de OpenID Connect-koppeling voor eHerkenning is ingeschakeld (zie sectie 10.6),
   vervangt deze de SAML-koppeling op de loginpagina. Beide kunnen niet tegelijkertijd
   actief zijn.

10.4. KVK configuratie
======================

Dit is de configuratie voor de koppeling van het Open Inwoner platform met de KVK. Om Mijn Bedrijven te kunnen gebruiken is het noodzakelijk om de KVK API in te stellen. Hierdoor worden – na het inloggen met eHerkenning - de gegevens van het bedrijf opgehaald en getoond en vooraf ingevuld. Om de KVK API in te kunnen stellen zijn de API key, een client certificate (SSL) en een server certificate (SSL) noodzakelijk.

.. image:: images/Screenshot_OIP_inlogkoppelingen_KVKconfiguratie_Djuzz_250829.png
   :width: 624px

**API root**
De API root is verschillend voor de testomgeving en de productieomgeving van Open Inwoner. Bij de testomgeving moet de root https://developers.kvk.nl/test/api/ zijn en bij de productieomgeving https://api.kvk.nl/api/v2

Let op! Er is een abonnement noodzakelijk om gebruik te kunnen maken van deze API. Meer informatie over de KVK API kunt u vinden op: https://developers.kvk.nl/documentation

**API Key**
De API Key ontvangt u wanneer u zich aanmeldt om gebruik te maken van de KVK API.

**Client certificate**
Het SSL-certificaat dat wordt gebruikt voor clientidentificatie. Dit veld kan leeg blijven.

**Server certificate**
Het SSL/TLS certificaat van de server. Dit certificaat kunt u downloaden van de KVK
website: https://developers.kvk.nl/documentation/certificates

Het gedownloade zip-bestand bevat meerdere certificaat bestanden die u moet combineren
tot één bestand:

1. Pak het zip-bestand uit
2. Combineer alle ``.crt`` bestanden tot één bestand via de commandline:

   .. code-block:: bash

      cat bestand1.crt bestand2.crt bestand3.crt > combined.crt

   Bijvoorbeeld (bestandsnamen kunnen afwijken):

   .. code-block:: bash

      cat api.kvk.nl.crt "DigiCert G2 TLS EU RSA4096 SHA384 2022 CA1.crt" \
          "DigiCert Global Root G2.crt" > combined.crt

3. Upload het gecombineerde bestand bij **Server certificate** door een bestand
   certificaat bij te werken (potlood icoon) of een nieuw certificaat toe te voegen
   (via het plus icoon).

10.5. OpenID Connect configuratie voor DigiD
============================================

Open Inwoner ondersteunt DigiD-login voor burgers via het OpenID Connect protocol (OIDC).
Dit is een alternatief voor de SAML-gebaseerde DigiD-koppeling. OIDC staat standaard
uitgeschakeld en vereist technische configuratie voordat het in gebruik genomen kan worden.

**Let op! Enkel de technisch beheerder dient de OpenID Connect Configuratie te wijzigen.**

.. image:: images/image77.png
   :width: 620px
   :height: 333px

*Activatie*

**Inschakelen**
Schakelt DigiD-login via OIDC in of uit. Staat standaard uitgeschakeld.

.. note::

   Wanneer ingeschakeld, vervangt de OIDC-koppeling de SAML-gebaseerde DigiD-koppeling
   op de loginpagina. Beide kunnen niet tegelijkertijd actief zijn.

*Algemene instellingen*

**OpenID Connect client ID**
Het client-ID verstrekt door de OIDC-provider (identity broker).

**OpenID Connect secret**
Het bijbehorende client-secret van de OIDC-provider.

**OpenID Connect scopes**
De scopes die worden aangevraagd bij de identity provider. Standaard: ``openid``, ``bsn``.

**Ondertekeningsalgoritme**
Algoritme waarmee de provider ID-tokens ondertekent. Standaard ``HS256``; gebruik ``RS256`` bij een asymmetrisch sleutelpaar.

**Ondertekeningssleutel**
Openbare sleutel van de provider in PEM- of DER-formaat. Alleen vereist bij RSA-algoritmen zoals ``RS256``.

*Attributen uit claims*

**BSN claim**
Naam van de claim die het BSN van de gebruiker bevat. Standaard: ``bsn``.

**LoA claim**
Naam van de claim met het betrouwbaarheidsniveau (Level of Assurance). Laat leeg als de provider geen LoA levert; de standaardwaarde hieronder wordt dan gebruikt.

**Standaard LoA**
Het betrouwbaarheidsniveau dat wordt toegepast als de identity provider geen LoA-claim
meestuurt in het token. Het betrouwbaarheidsniveau bepaalt welke acties een ingelogde
gebruiker mag uitvoeren - een hoger niveau vereist een sterkere vorm van authenticatie.

**LoA-mapping**
Vertaaltabel voor LoA-claimwaarden van de provider naar Nederlandse standaardniveaus. Gebruik dit als de provider eigen waarden hanteert.

*Eindpunten*

**Discovery endpoint**
URL van het discovery-endpoint van de provider. Het pad ``.well-known/openid-configuration``
wordt automatisch toegevoegd. Als dit is ingevuld, kunnen de overige eindpunten worden
weggelaten - ze worden automatisch afgeleid bij het opslaan van de configuratie.

.. note::

   Als er geen discovery-endpoint beschikbaar is, kunnen de onderstaande velden handmatig
   worden ingevuld.

**JSON Web Key Set endpoint**
URL van het JWKS-endpoint. Verplicht bij gebruik van het ``RS256``-algoritme.

**Authorization endpoint**
URL van het autorisatie-endpoint van de provider.

**Token endpoint**
URL van het token-endpoint van de provider.

**Gebruik Basic auth voor token endpoint**
Indien ingeschakeld worden client-ID en secret via HTTP Basic auth meegestuurd bij het
ophalen van het access token. Standaard worden ze in de request body geplaatst.

**User endpoint**
URL van het userinfo-endpoint van de provider.

**Logout endpoint**
URL van het logout-endpoint van de provider. Optioneel.

*Keycloak-specifieke instellingen*

**Keycloak Identity Provider hint**
Alleen van toepassing bij Keycloak: geeft aan welke identity provider gebruikt moet worden,
zodat het Keycloak-loginscherm wordt overgeslagen. Laat leeg bij andere providers.

*Geavanceerde instellingen*

.. _digid-oidc-userinfo-bron:

**Gebruikersinformatie claims afkomstig van**
Bepaalt vanwaar de gebruikersclaims worden opgehaald: het *Userinfo endpoint* (standaard)
of het *ID-token*. Kies *Userinfo endpoint* wanneer de identity provider de claims niet
in het ID-token zelf meelevert.

**Nonce verificatie**
Schakelt nonce-verificatie in of uit (standaard ingeschakeld).

**Nonce-grootte** / **State-grootte**
Lengte van de willekeurige nonce- en state-strings (standaard: 32 tekens).

Signicat (eID Hub, nieuwe stijl)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Signicat <https://www.signicat.com/>`_ is een veelgebruikte identity broker voor
DigiD en eHerkenning via OIDC. Onderstaande instellingen zijn de aanbevolen configuratie
voor gebruik met Open Inwoner. Deze instructies gaan uit van de **eID and Wallet Hub**
(nieuwe stijl), niet de legacy-omgeving.

- Log in op https://dashboard.signicat.com/
- Ga naar de **eID and Wallet Hub**
- Klik op **Add Client**:

  - **Client name**: een beschrijvende naam, bij voorkeur:
    ``{gemeente}-open-inwoner-{acceptatie,productie}``
  - **Redirect URI**: de basis-URL van de deploy, zonder verdere paden, bijvoorbeeld
    ``https://open-inwoner-test.maykin.nl``

- Tabblad **URIs**:

  - **Redirect URIs** - voeg de volgende drie toe (pas de basis-URL aan):

    - ``https://open-inwoner-test.maykin.nl/digid-oidc/callback/``
    - ``https://open-inwoner-test.maykin.nl/eherkenning-oidc/callback/``
    - ``https://open-inwoner-test.maykin.nl/eidas-oidc/callback/``

  - **Post logout Redirect URIs**:

    - ``https://open-inwoner-test.maykin.nl/accounts/login/``

  - **Front Channel Logout URI**:

    - ``https://open-inwoner-test.maykin.nl/accounts/login/``

  - **Required Front Channel Logout Session**: uitgevinkt
  - **Automatic Redirect to Logout URL**: aangevinkt

- Tabblad **Secrets**:

  - Maak één secret aan met een beschrijvende naam (gebruik bijvoorbeeld de URL van de doelomgeving)
  - Kopieer de client secret naar het daartoe bestemde veld in Open Inwoner

- Tabblad **Access**:

  - **Allowed scopes**:
    - ``openid``
    - ``eherkenning-extra``
    - ``idp-id``
    - ``profile``
  - **Identity provider restrictions**: leeg laten
  - **ACR values**: leeg laten
  - **Force use ACR values**: leeg laten

- Tabblad **Advanced**:

  - Sectie **Security**:

    - **ID Token User data**: ``Minimal``

      .. note::

         Omdat Signicat met deze instelling de claims niet in het ID-token meelevert,
         moet in Open Inwoner onder *Geavanceerde instellingen* de optie
         **Gebruikersinformatie claims afkomstig van** worden ingesteld op
         *Userinfo endpoint*. Dit veld is te vinden in de DigiD- en
         eHerkenning OIDC-configuratiepagina's in de beheeromgeving.

    - **User Info Response Type**: ``JSON``
    - **Content encryption algorithm**: ``A128CBC-HS256``
    - **Allowed CORS Origins**: leeg laten
    - **Requires Secret**: aanvinken; alle overige checkboxes uitvinken

10.5.1. Geschiedenis
--------------------

Wanneer er wijzigingen aan de OpenID Connect configuratie hebben plaatsgevonden, kunnen deze worden nagetrokken in de geschiedenis rechts bovenin beeld.

10.6. OpenID Connect configuratie voor eHerkenning
==================================================

Open Inwoner ondersteunt eHerkenning-login voor ondernemers via het OpenID Connect protocol
(OIDC). Dit is een alternatief voor de SAML-gebaseerde eHerkenning-koppeling. OIDC staat
standaard uitgeschakeld en vereist technische configuratie voordat het in gebruik genomen
kan worden.

**Let op! Enkel de technisch beheerder dient de OpenID Connect Configuratie te wijzigen.**

*Activatie*

**Inschakelen**
Schakelt eHerkenning-login via OIDC in of uit. Staat standaard uitgeschakeld.

.. note::

   Wanneer ingeschakeld, vervangt de OIDC-koppeling de SAML-gebaseerde
   eHerkenning-koppeling op de loginpagina. Beide kunnen niet tegelijkertijd actief zijn.

*Algemene instellingen*

**OpenID Connect client ID**
Het client-ID verstrekt door de OIDC-provider (identity broker).

**OpenID Connect secret**
Het bijbehorende client-secret van de OIDC-provider.

**OpenID Connect scopes**
De scopes die worden aangevraagd bij de identity provider. Standaard: ``openid``, ``kvk``.

**Ondertekeningsalgoritme**
Algoritme waarmee de provider ID-tokens ondertekent. Standaard ``HS256``; gebruik ``RS256`` bij een asymmetrisch sleutelpaar.

**Ondertekeningssleutel**
Openbare sleutel van de provider in PEM- of DER-formaat. Alleen vereist bij RSA-algoritmen zoals ``RS256``.

*Attributen uit claims*

**Identifier type claim**
Naam van de claim die aangeeft hoe de bedrijfsidentifier geïnterpreteerd moet worden.
Verwachte waarden: ``urn:etoegang:1.9:EntityConcernedID:KvKnr`` (KVK-nummer) of
``urn:etoegang:1.9:EntityConcernedID:RSIN``. Standaard: ``namequalifier``.

**Bedrijfsidentifier claim**
Naam van de claim met het KVK-nummer of RSIN van het ingelogde bedrijf.
Standaard: ``urn:etoegang:core:LegalSubjectID``.

**Vestigingsnummer claim**
Naam van de claim met het vestigingsnummer, indien van toepassing.
Standaard: ``urn:etoegang:1.9:ServiceRestriction:Vestigingsnr``.

**Vertegenwoordiger claim**
Naam van de claim met de (pseudonieme) identifier van de gebruiker die namens het
bedrijf handelt. Standaard: ``urn:etoegang:core:ActingSubjectID``.

**LoA claim**
Naam van de claim met het betrouwbaarheidsniveau (Level of Assurance). Laat leeg als de provider geen LoA levert; de standaardwaarde hieronder wordt dan gebruikt.

**Standaard LoA**
Het betrouwbaarheidsniveau dat wordt toegepast als de identity provider geen LoA-claim meestuurt in het token. Het betrouwbaarheidsniveau bepaalt welke acties een ingelogde gebruiker mag uitvoeren - een hoger niveau vereist een sterkere vorm van authenticatie.

**LoA-mapping**
Vertaaltabel voor LoA-claimwaarden van de provider naar Nederlandse standaardniveaus. Gebruik dit als de provider eigen waarden hanteert.

*Eindpunten*

**Discovery endpoint**
URL van het discovery-endpoint van de provider. Het pad ``.well-known/openid-configuration``
wordt automatisch toegevoegd. Als dit is ingevuld, kunnen de overige eindpunten worden
weggelaten - ze worden automatisch afgeleid bij het opslaan van de configuratie. Als er
geen discovery-endpoint beschikbaar is, kunnen de onderstaande velden handmatig worden
ingevuld.

**JSON Web Key Set endpoint**
URL van het JWKS-endpoint. Verplicht bij gebruik van het ``RS256``-algoritme.

**Authorization endpoint**
URL van het autorisatie-endpoint van de provider.

**Token endpoint**
URL van het token-endpoint van de provider.

**Gebruik Basic auth voor token endpoint**
Indien ingeschakeld worden client-ID en secret via HTTP Basic auth meegestuurd bij het
ophalen van het access token. Standaard worden ze in de request body geplaatst.

**User endpoint**
URL van het userinfo-endpoint van de provider.

**Logout endpoint**
URL van het logout-endpoint van de provider. Optioneel.

*Keycloak-specifieke instellingen*

**Keycloak Identity Provider hint**
Alleen van toepassing bij Keycloak: geeft aan welke identity provider gebruikt moet worden,
zodat het Keycloak-loginscherm wordt overgeslagen. Laat leeg bij andere providers.

*Geavanceerde instellingen*

**Gebruikersinformatie claims afkomstig van**
Bepaalt vanwaar de gebruikersclaims worden opgehaald: het *Userinfo endpoint* (standaard)
of het *ID-token*. Zie sectie 10.5 voor een toelichting.

**Nonce verificatie**
Schakelt nonce-verificatie in of uit (standaard ingeschakeld).

**Nonce-grootte** / **State-grootte**
Lengte van de willekeurige nonce- en state-strings (standaard: 32 tekens).

10.7. OpenID Connect sessie management
=======================================

Bij gebruik van OpenID Connect (OIDC) voor DigiD en eHerkenning is het belangrijk om
rekening te houden met sessie-management. Open Inwoner vernieuwt periodiek de
authenticatiesessie om te controleren of de gebruiker nog steeds ingelogd is bij de
Identity Provider (IdP).

10.7.1. Automatische sessievernieuwing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

De omgevingsvariabele ``OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS`` bepaalt hoe vaak
de sessie wordt ververst. De standaardwaarde is **15 minuten**. Na deze periode wordt de
gebruiker automatisch en onzichtbaar doorgestuurd naar de IdP:

- **Als de IdP-sessie nog actief is**: De gebruiker wordt automatisch teruggestuurd naar
  Open Inwoner en kan ongestoord doorwerken. Dit gebeurt op de achtergrond zonder dat de
  gebruiker het merkt.

- **Als de IdP-sessie verlopen is**: De gebruiker wordt uitgelogd en krijgt een
  foutmelding te zien:

  - DigiD: *"Uw DigiD-sessie is verlopen. Log alstublieft opnieuw in."*
  - eHerkenning: *"Uw eHerkenning-sessie is verlopen. Log alstublieft opnieuw in."*

.. important::

   Stel de sessieduur bij uw Identity Provider (DigiD/eHerkenning) in op **minimaal de
   duur van één vernieuwingsinterval langer** dan ``OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS``.
   Bij voorkeur zelfs aanzienlijk langer om te voorkomen dat gebruikers onverwacht worden
   uitgelogd tijdens het werken. Houd hierbij rekening met de eisen en aanbevelingen van
   Logius en uw identity broker (bijvoorbeeld Signicat).

   Bijvoorbeeld:

   - Als ``OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS`` is ingesteld op 10 minuten (600 seconden)
   - Stel de IdP-sessieduur in op minimaal 21 minuten of langer, zodat de gebruiker tot
     tweemaal toe de sessie kan laten vernieuwen.

   Als de IdP-sessieduur korter is dan het vernieuwingsinterval, kunnen gebruikers
   onverwacht worden uitgelogd. Let ook op dat een korter vernieuwingsinterval betekent
   dat er vaker een redirect plaatsvindt naar de IdP. Hierdoor is de kans groter dat
   een redirect gebeurt tijdens het versturen van een formulier (POST-verzoek), wat kan
   leiden tot verlies van ingevulde gegevens.
