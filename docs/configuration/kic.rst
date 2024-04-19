.. _kic:

=====================
Klanten Configuration
=====================

Settings Overview
=================

Required:
"""""""""

::

    KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_ID
    KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_SECRET
    KIC_CONFIG_CONTACTMOMENTEN_API_ROOT
    KIC_CONFIG_KLANTEN_API_CLIENT_ID
    KIC_CONFIG_KLANTEN_API_CLIENT_SECRET
    KIC_CONFIG_KLANTEN_API_ROOT
    KIC_CONFIG_REGISTER_CONTACT_MOMENT
    KIC_CONFIG_REGISTER_TYPE


All settings:
"""""""""""""

::

    KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_ID
    KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_SECRET
    KIC_CONFIG_CONTACTMOMENTEN_API_ROOT
    KIC_CONFIG_KLANTEN_API_CLIENT_ID
    KIC_CONFIG_KLANTEN_API_CLIENT_SECRET
    KIC_CONFIG_KLANTEN_API_ROOT
    KIC_CONFIG_REGISTER_BRONORGANISATIE_RSIN
    KIC_CONFIG_REGISTER_CHANNEL
    KIC_CONFIG_REGISTER_CONTACT_MOMENT
    KIC_CONFIG_REGISTER_EMAIL
    KIC_CONFIG_REGISTER_EMPLOYEE_ID
    KIC_CONFIG_REGISTER_TYPE
    KIC_CONFIG_SEND_EMAIL_CONFIRMATION
    KIC_CONFIG_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER


Detailed Information
====================

::

    Variable            KIC_CONFIG_REGISTER_EMAIL
    Setting             Registreer op email adres
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_CONTACT_MOMENT
    Setting             Registreer in Contactmomenten API
    Description         No description
    Possible values     True, False
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_BRONORGANISATIE_RSIN
    Setting             Organisatie RSIN
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_CHANNEL
    Setting             Contactmoment kanaal
    Description         De kanaal waarop nieuwe contactmomenten worden aangemaakt
    Possible values     string
    Default value       contactformulier
    
    Variable            KIC_CONFIG_REGISTER_TYPE
    Setting             Contactmoment type
    Description         Naam van 'contacttype' uit e-Suite
    Possible values     string
    Default value       Melding
    
    Variable            KIC_CONFIG_REGISTER_EMPLOYEE_ID
    Setting             Medewerker identificatie
    Description         Gebruikersnaam van actieve medewerker uit e-Suite
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER
    Setting             Haal bronnen op uit de Klanten- en Contactmomenten-API's voor gebruikers die zijn geauthenticeerd met eHerkenning via RSIN
    Description         Indien ingeschakeld, worden bronnen uit de Klanten- en Contactmomenten-API's voor eHerkenning-gebruikers opgehaald via RSIN (Open Klant). Indien niet ingeschakeld, worden deze bronnen via het KVK-nummer.
    Possible values     True, False
    Default value       No default
    
    Variable            KIC_CONFIG_SEND_EMAIL_CONFIRMATION
    Setting             Stuur contactformulier e-mailbevestiging
    Description         Indien ingeschakeld dan wordt het 'contactform_confimation' e-mailsjabloon gebruikt om een e-mailbevestiging te sturen na het insturen van het contactformulier. Indien uitgeschakeld dan wordt aangenomen dat de externe contactmomenten API (eg. eSuite) de e-mailbevestiging zal sturen
    Possible values     True, False
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_ID
    Setting             Client ID of the Contactmomenten API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_SECRET
    Setting             Client Secret of the Contactmomenten API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_API_ROOT
    Setting             Root URL of the Contactmomenten API
    Description         No description
    Possible values     string (URL)
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_API_CLIENT_ID
    Setting             Client ID of the Klanten API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_API_CLIENT_SECRET
    Setting             Client Secret of the Klanten API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_API_ROOT
    Setting             Root URL of the Klanten API
    Description         No description
    Possible values     string (URL)
    Default value       No default
