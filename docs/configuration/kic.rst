.. _kic:


=====================
Klanten configuration
=====================


Settings Overview
=================

Required:
"""""""""

::

    KIC_CONFIG_KLANTEN_API_ROOT
    KIC_CONFIG_KLANTEN_API_CLIENT_ID
    KIC_CONFIG_KLANTEN_API_CLIENT_SECRET
    KIC_CONFIG_CONTACTMOMENTEN_API_ROOT
    KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_ID
    KIC_CONFIG_CONTACTMOMENTEN_API_CLIENT_SECRET
    KIC_CONFIG_REGISTER_TYPE
    KIC_CONFIG_REGISTER_CONTACT_MOMENT
    


All settings:
"""""""""""""

::

    KIC_CONFIG_REGISTER_EMAIL
    KIC_CONFIG_REGISTER_CONTACT_MOMENT
    KIC_CONFIG_REGISTER_BRONORGANISATIE_RSIN
    KIC_CONFIG_REGISTER_CHANNEL
    KIC_CONFIG_REGISTER_TYPE
    KIC_CONFIG_REGISTER_EMPLOYEE_ID
    KIC_CONFIG_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER
    

Detailed Information
====================

::

    
    Variable            KIC_CONFIG_REGISTER_EMAIL
    Setting             Registreer op email adres
    Description         
    Possible values     string (Email)
    
    
    Variable            KIC_CONFIG_REGISTER_CONTACT_MOMENT
    Setting             Registreer in Contactmomenten API
    Description         
    Possible values     True, False
    
    
    Variable            KIC_CONFIG_REGISTER_BRONORGANISATIE_RSIN
    Setting             Organisatie RSIN
    Description         
    Possible values     string
    
    
    Variable            KIC_CONFIG_REGISTER_CHANNEL
    Setting             Contactmoment kanaal
    Description         The channel through which contactmomenten are created
    Possible values     string
    
    
    Variable            KIC_CONFIG_REGISTER_TYPE
    Setting             Contactmoment type
    Description         Naam van 'contacttype' uit e-Suite
    Possible values     string
    
    
    Variable            KIC_CONFIG_REGISTER_EMPLOYEE_ID
    Setting             Medewerker identificatie
    Description         Gebruikersnaam van actieve medewerker uit e-Suite
    Possible values     string
    
    
    Variable            KIC_CONFIG_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER
    Setting             Haal bronnen op uit de Klanten- en Contactmomenten-API's voor gebruikers die zijn geauthenticeerd met eHerkenning via RSIN
    Description         Indien ingeschakeld, worden bronnen uit de Klanten- en Contactmomenten-API's voor eHerkenning-gebruikers opgehaald via RSIN (Open Klant). Indien niet ingeschakeld, worden deze bronnen via het KVK-nummer.
    Possible values     True, False
    
    