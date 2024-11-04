.. _kic:

==================================
Klantinteractie APIs configuration
==================================

Settings Overview
=================


Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    KIC_CONFIG_ENABLE



Required:
"""""""""

::

    KIC_CONTACTMOMENTEN_SERVICE_API_ROOT
    KIC_CONTACTMOMENTEN_SERVICE_CLIENT_ID
    KIC_CONTACTMOMENTEN_SERVICE_SECRET
    KIC_KLANTEN_SERVICE_API_ROOT
    KIC_KLANTEN_SERVICE_CLIENT_ID
    KIC_KLANTEN_SERVICE_SECRET
    KIC_SERVER_CERTIFICATE_LABEL
    KIC_SERVER_CERTIFICATE_TYPE


All settings:
"""""""""""""

::

    KIC_CONTACTMOMENTEN_SERVICE_API_ROOT
    KIC_CONTACTMOMENTEN_SERVICE_CLIENT_ID
    KIC_CONTACTMOMENTEN_SERVICE_SECRET
    KIC_KLANTEN_SERVICE_API_ROOT
    KIC_KLANTEN_SERVICE_CLIENT_ID
    KIC_KLANTEN_SERVICE_SECRET
    KIC_REGISTER_BRONORGANISATIE_RSIN
    KIC_REGISTER_CHANNEL
    KIC_REGISTER_CONTACT_MOMENT
    KIC_REGISTER_CONTACT_MOMENT
    KIC_REGISTER_EMAIL
    KIC_REGISTER_EMPLOYEE_ID
    KIC_REGISTER_TYPE
    KIC_SERVER_CERTIFICATE_LABEL
    KIC_SERVER_CERTIFICATE_TYPE
    KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER

Detailed Information
====================

::

    Variable            KIC_CONTACTMOMENTEN_SERVICE_API_CLIENT_ID
    Description         The client ID of the klant contactmomenten service
    Possible values     string (URL)
    Default value       No default
    
    Variable            KIC_CONTACTMOMENTEN_SERVICE_API_ROOT
    Description         The API root of the klant contactmomenten service
    Possible values     string (URL)
    Default value       No default
    
    Variable            KIC_CONTACTMOMENTEN_SERVICE_SECRET
    Description         The secret of the klant contactmomenten service
    Possible values     string (URL)
    Default value       No default
    
    Variable            KIC_KLANTEN_SERVICE_API_CLIENT_ID
    Description         The API root of the klanten service
    Possible values     string (URL)
    Default value       No default
    
    Variable            KIC_KLANTEN_SERVICE_API_ROOT
    Description         The API root of the klanten service
    Possible values     string (URL)
    Default value       No default
    
    Variable            KIC_KLANTEN_SERVICE_SECRET
    Description         The secret of the klanten service
    Possible values     string (URL)
    Default value       No default
    
    Variable            KIC_REGISTER_BRONORGANISATIE_RSIN
    Setting             Organisatie RSIN
    Description         No description
    Possible values     string
    Default value       
    
    Variable            KIC_REGISTER_CHANNEL
    Setting             Contactmoment kanaal
    Description         De kanaal waarop nieuwe contactmomenten worden aangemaakt
    Possible values     string
    Default value       contactformulier
    
    Variable            KIC_REGISTER_CONTACT_MOMENT
    Setting             Registreer in Contactmomenten API
    Description         No description
    Possible values     True, False
    Default value       False
    
    Variable            KIC_REGISTER_EMAIL
    Setting             Registreer op email adres
    Description         No description
    Possible values     string representing an Email address (foo@bar.com)
    Default value       No default
    
    Variable            KIC_REGISTER_EMPLOYEE_ID
    Setting             Medewerker identificatie
    Description         Gebruikersnaam van actieve medewerker uit e-Suite
    Possible values     string
    Default value       
    
    Variable            KIC_REGISTER_TYPE
    Setting             Contactmoment type
    Description         Naam van 'contacttype' uit e-Suite
    Possible values     string
    Default value       Melding
    
    Variable            KIC_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER
    Setting             Haal bronnen op uit de Klanten- en Contactmomenten-API's voor gebruikers die zijn geauthenticeerd met eHerkenning via RSIN
    Description         Indien ingeschakeld, worden bronnen uit de Klanten- en Contactmomenten-API's voor eHerkenning-gebruikers opgehaald via RSIN (Open Klant). Indien niet ingeschakeld, worden deze bronnen via het KVK-nummer.
    Possible values     True, False
    Default value       False
