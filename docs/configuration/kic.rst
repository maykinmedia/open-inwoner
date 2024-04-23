.. _kic:

=====================
Klanten Configuration
=====================

Settings Overview
=================

Required:
"""""""""

::

    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_API_ROOT
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_CLIENT_ID
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_SECRET
    KIC_CONFIG_KLANTEN_SERVICE_API_ROOT
    KIC_CONFIG_KLANTEN_SERVICE_CLIENT_ID
    KIC_CONFIG_KLANTEN_SERVICE_SECRET
    KIC_CONFIG_REGISTER_CONTACT_MOMENT
    KIC_CONFIG_REGISTER_TYPE


All settings:
"""""""""""""

::

    KIC_CONFIG_CLIENT_CERTIFICATE_ID
    KIC_CONFIG_CLIENT_CERTIFICATE_LABEL
    KIC_CONFIG_CLIENT_CERTIFICATE_PRIVATE_KEY
    KIC_CONFIG_CLIENT_CERTIFICATE_PUBLIC_CERTIFICATE
    KIC_CONFIG_CLIENT_CERTIFICATE_TYPE
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_API_ROOT
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_API_TYPE
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_AUTH_TYPE
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_CLIENT_ID
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_HEADER_KEY
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_HEADER_VALUE
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_ID
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_LABEL
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_NLX
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_OAS
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_OAS_FILE
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_SECRET
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_USER_ID
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_USER_REPRESENTATION
    KIC_CONFIG_CONTACTMOMENTEN_SERVICE_UUID
    KIC_CONFIG_ID
    KIC_CONFIG_KLANTEN_SERVICE_API_ROOT
    KIC_CONFIG_KLANTEN_SERVICE_API_TYPE
    KIC_CONFIG_KLANTEN_SERVICE_AUTH_TYPE
    KIC_CONFIG_KLANTEN_SERVICE_CLIENT_ID
    KIC_CONFIG_KLANTEN_SERVICE_HEADER_KEY
    KIC_CONFIG_KLANTEN_SERVICE_HEADER_VALUE
    KIC_CONFIG_KLANTEN_SERVICE_ID
    KIC_CONFIG_KLANTEN_SERVICE_LABEL
    KIC_CONFIG_KLANTEN_SERVICE_NLX
    KIC_CONFIG_KLANTEN_SERVICE_OAS
    KIC_CONFIG_KLANTEN_SERVICE_OAS_FILE
    KIC_CONFIG_KLANTEN_SERVICE_SECRET
    KIC_CONFIG_KLANTEN_SERVICE_USER_ID
    KIC_CONFIG_KLANTEN_SERVICE_USER_REPRESENTATION
    KIC_CONFIG_KLANTEN_SERVICE_UUID
    KIC_CONFIG_REGISTER_BRONORGANISATIE_RSIN
    KIC_CONFIG_REGISTER_CHANNEL
    KIC_CONFIG_REGISTER_CONTACT_MOMENT
    KIC_CONFIG_REGISTER_EMAIL
    KIC_CONFIG_REGISTER_EMPLOYEE_ID
    KIC_CONFIG_REGISTER_TYPE
    KIC_CONFIG_SEND_EMAIL_CONFIRMATION
    KIC_CONFIG_SERVER_CERTIFICATE_ID
    KIC_CONFIG_SERVER_CERTIFICATE_LABEL
    KIC_CONFIG_SERVER_CERTIFICATE_PRIVATE_KEY
    KIC_CONFIG_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE
    KIC_CONFIG_SERVER_CERTIFICATE_TYPE
    KIC_CONFIG_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER


Detailed Information
====================

::

    Variable            KIC_CONFIG_KLANTEN_SERVICE_SECRET
    Setting             secret
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_API_ROOT
    Setting             api root url
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_SERVER_CERTIFICATE_TYPE
    Setting             type
    Description         Is this only a certificate or is there an associated private key?
    Possible values     key_pair, cert_only
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_CLIENT_ID
    Setting             client id
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_HEADER_KEY
    Setting             header key
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_OAS_FILE
    Setting             OAS file
    Description         OAS yaml file
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_OAS
    Setting             OAS url
    Description         URL to OAS yaml file
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_ID
    Setting             ID
    Description         No description
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_CLIENT_CERTIFICATE_PUBLIC_CERTIFICATE
    Setting             public certificate
    Description         The content of the certificate
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_SECRET
    Setting             secret
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_SEND_EMAIL_CONFIRMATION
    Setting             Stuur contactformulier e-mailbevestiging
    Description         Indien ingeschakeld dan wordt het 'contactform_confimation' e-mailsjabloon gebruikt om een e-mailbevestiging te sturen na het insturen van het contactformulier. Indien uitgeschakeld dan wordt aangenomen dat de externe contactmomenten API (eg. eSuite) de e-mailbevestiging zal sturen
    Possible values     True, False
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_AUTH_TYPE
    Setting             authorization type
    Description         No description
    Possible values     no_auth, api_key, zgw
    Default value       zgw
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_NLX
    Setting             NLX url
    Description         NLX (outway) address
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_BRONORGANISATIE_RSIN
    Setting             Organisatie RSIN
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CLIENT_CERTIFICATE_TYPE
    Setting             type
    Description         Is this only a certificate or is there an associated private key?
    Possible values     key_pair, cert_only
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_OAS_FILE
    Setting             OAS file
    Description         OAS yaml file
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_SERVER_CERTIFICATE_LABEL
    Setting             label
    Description         Recognisable label for the certificate
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_UUID
    Setting             UUID
    Description         No description
    Possible values     No information available
    Default value       98df2dde-736c-4d54-b0d0-c3c46df9ad1b
    
    Variable            KIC_CONFIG_SERVER_CERTIFICATE_PRIVATE_KEY
    Setting             private key
    Description         The content of the private key
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_EMPLOYEE_ID
    Setting             Medewerker identificatie
    Description         Gebruikersnaam van actieve medewerker uit e-Suite
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_TYPE
    Setting             Contactmoment type
    Description         Naam van 'contacttype' uit e-Suite
    Possible values     string
    Default value       Melding
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_API_ROOT
    Setting             api root url
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_SERVER_CERTIFICATE_PUBLIC_CERTIFICATE
    Setting             public certificate
    Description         The content of the certificate
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_CLIENT_CERTIFICATE_PRIVATE_KEY
    Setting             private key
    Description         The content of the private key
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_HEADER_VALUE
    Setting             header value
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_HEADER_KEY
    Setting             header key
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CLIENT_CERTIFICATE_LABEL
    Setting             label
    Description         Recognisable label for the certificate
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_CONTACT_MOMENT
    Setting             Registreer in Contactmomenten API
    Description         No description
    Possible values     True, False
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_CHANNEL
    Setting             Contactmoment kanaal
    Description         De kanaal waarop nieuwe contactmomenten worden aangemaakt
    Possible values     string
    Default value       contactformulier
    
    Variable            KIC_CONFIG_CLIENT_CERTIFICATE_ID
    Setting             ID
    Description         No description
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_SERVER_CERTIFICATE_ID
    Setting             ID
    Description         No description
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_LABEL
    Setting             label
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_ID
    Setting             ID
    Description         No description
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_HEADER_VALUE
    Setting             header value
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_USE_RSIN_FOR_INNNNPID_QUERY_PARAMETER
    Setting             Haal bronnen op uit de Klanten- en Contactmomenten-API's voor gebruikers die zijn geauthenticeerd met eHerkenning via RSIN
    Description         Indien ingeschakeld, worden bronnen uit de Klanten- en Contactmomenten-API's voor eHerkenning-gebruikers opgehaald via RSIN (Open Klant). Indien niet ingeschakeld, worden deze bronnen via het KVK-nummer.
    Possible values     True, False
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_ID
    Setting             ID
    Description         No description
    Possible values     No information available
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_CLIENT_ID
    Setting             client id
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_USER_ID
    Setting             user ID
    Description         User ID to use for the audit trail. Although these external API credentials are typically used bythis API itself instead of a user, the user ID is required.
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_LABEL
    Setting             label
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_NLX
    Setting             NLX url
    Description         NLX (outway) address
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_API_TYPE
    Setting             type
    Description         No description
    Possible values     ac, nrc, zrc, ztc, drc, brc, cmc, kc, vrc, orc
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_UUID
    Setting             UUID
    Description         No description
    Possible values     No information available
    Default value       d130d5a3-fe6b-4930-8b7d-4ffd99fa5a7a
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_USER_ID
    Setting             user ID
    Description         User ID to use for the audit trail. Although these external API credentials are typically used bythis API itself instead of a user, the user ID is required.
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_OAS
    Setting             OAS url
    Description         URL to OAS yaml file
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_USER_REPRESENTATION
    Setting             user representation
    Description         Human readable representation of the user.
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_REGISTER_EMAIL
    Setting             Registreer op email adres
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_AUTH_TYPE
    Setting             authorization type
    Description         No description
    Possible values     no_auth, api_key, zgw
    Default value       zgw
    
    Variable            KIC_CONFIG_KLANTEN_SERVICE_USER_REPRESENTATION
    Setting             user representation
    Description         Human readable representation of the user.
    Possible values     string
    Default value       No default
    
    Variable            KIC_CONFIG_CONTACTMOMENTEN_SERVICE_API_TYPE
    Setting             type
    Description         No description
    Possible values     ac, nrc, zrc, ztc, drc, brc, cmc, kc, vrc, orc
    Default value       No default
