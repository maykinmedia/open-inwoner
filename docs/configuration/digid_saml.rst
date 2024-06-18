.. _digid_saml:

================================
Configuration for DigiD via SAML
================================

Settings Overview
=================


Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    DIGID_SAML_CONFIG_ENABLE



Required:
"""""""""

::

    DIGID_SAML_BASE_URL
    DIGID_SAML_CERTIFICATE_LABEL
    DIGID_SAML_CERTIFICATE_PUBLIC_CERTIFICATE
    DIGID_SAML_CERTIFICATE_TYPE
    DIGID_SAML_ENTITY_ID
    DIGID_SAML_METADATA_FILE_SOURCE
    DIGID_SAML_SERVICE_DESCRIPTION
    DIGID_SAML_SERVICE_NAME


All settings:
"""""""""""""

::

    DIGID_SAML_ARTIFACT_RESOLVE_CONTENT_TYPE
    DIGID_SAML_ATTRIBUTE_CONSUMING_SERVICE_INDEX
    DIGID_SAML_BASE_URL
    DIGID_SAML_CERTIFICATE_LABEL
    DIGID_SAML_CERTIFICATE_PRIVATE_KEY
    DIGID_SAML_CERTIFICATE_PUBLIC_CERTIFICATE
    DIGID_SAML_CERTIFICATE_TYPE
    DIGID_SAML_DIGEST_ALGORITHM
    DIGID_SAML_ENTITY_ID
    DIGID_SAML_KEY_PASSPHRASE
    DIGID_SAML_METADATA_FILE_SOURCE
    DIGID_SAML_ORGANIZATION_NAME
    DIGID_SAML_ORGANIZATION_URL
    DIGID_SAML_REQUESTED_ATTRIBUTES
    DIGID_SAML_SERVICE_DESCRIPTION
    DIGID_SAML_SERVICE_NAME
    DIGID_SAML_SIGNATURE_ALGORITHM
    DIGID_SAML_SLO
    DIGID_SAML_TECHNICAL_CONTACT_PERSON_EMAIL
    DIGID_SAML_TECHNICAL_CONTACT_PERSON_TELEPHONE
    DIGID_SAML_WANT_ASSERTIONS_ENCRYPTED
    DIGID_SAML_WANT_ASSERTIONS_SIGNED

Detailed Information
====================

::

    Variable            DIGID_SAML_ARTIFACT_RESOLVE_CONTENT_TYPE
    Setting             Content-Type 'resolve artifact binding'
    Description         'application/soap+xml' wordt als 'legacy' beschouwd. Moderne brokers verwachten typisch 'text/xml'.
    Possible values     application/soap+xml, text/xml
    Default value       application/soap+xml
    
    Variable            DIGID_SAML_ATTRIBUTE_CONSUMING_SERVICE_INDEX
    Setting             Attribute consuming service index
    Description         Attribute consuming service index
    Possible values     string
    Default value       1
    
    Variable            DIGID_SAML_BASE_URL
    Setting             Basis-URL
    Description         De basis-URL van de applicatie, zonder slash op het eind.
    Possible values     string (URL)
    Default value       No default
    
    Variable            DIGID_SAML_CERTIFICATE_LABEL
    Setting             label
    Description         Recognisable label for the certificate
    Possible values     string
    Default value       No default
    
    Variable            DIGID_SAML_CERTIFICATE_PRIVATE_KEY
    Setting             private key
    Description         The content of the private key
    Possible values     No information available
    Default value       No default
    
    Variable            DIGID_SAML_CERTIFICATE_PUBLIC_CERTIFICATE
    Setting             public certificate
    Description         The content of the certificate
    Possible values     No information available
    Default value       No default
    
    Variable            DIGID_SAML_CERTIFICATE_TYPE
    Setting             type
    Description         Is this only a certificate or is there an associated private key?
    Possible values     key_pair, cert_only
    Default value       No default
    
    Variable            DIGID_SAML_DIGEST_ALGORITHM
    Setting             digest algorithm
    Description         Digest algorithm. Note that SHA1 is deprecated, but still the default value in the SAMLv2 standard. Warning: there are known issues with single-logout functionality if using anything other than SHA1 due to some hardcoded algorithm.
    Possible values     http://www.w3.org/2000/09/xmldsig#sha1, http://www.w3.org/2001/04/xmlenc#sha256, http://www.w3.org/2001/04/xmldsig-more#sha384, http://www.w3.org/2001/04/xmlenc#sha512
    Default value       http://www.w3.org/2000/09/xmldsig#sha1
    
    Variable            DIGID_SAML_ENTITY_ID
    Setting             entity ID
    Description         Service provider entity ID.
    Possible values     string
    Default value       No default
    
    Variable            DIGID_SAML_KEY_PASSPHRASE
    Setting             wachtwoordzin private-key
    Description         Wachtwoord voor de private-key voor de authenticatie-flow.
    Possible values     string
    Default value       No default
    
    Variable            DIGID_SAML_METADATA_FILE_SOURCE
    Setting             (XML) metadata-URL
    Description         De URL waar het XML metadata-bestand kan gedownload worden.
    Possible values     string (URL)
    Default value       
    
    Variable            DIGID_SAML_ORGANIZATION_NAME
    Setting             organisatienaam
    Description         Naam van de organisatie die de service aanbiedt waarvoor DigiD/eHerkenning/eIDAS-authenticatie ingericht is. Je moet ook de URL opgeven voor dit in de metadata beschikbaar is.
    Possible values     string
    Default value       No default
    
    Variable            DIGID_SAML_ORGANIZATION_URL
    Setting             organisatie-URL
    Description         URL van de organisatie die de service aanbiedt waarvoor DigiD/eHerkenning/eIDAS-authenticatie ingericht is. Je moet ook de organisatienaam opgeven voor dit in de metadata beschikbaar is.
    Possible values     string (URL)
    Default value       No default
    
    Variable            DIGID_SAML_REQUESTED_ATTRIBUTES
    Setting             gewenste attributen
    Description         Een lijst van strings (of objecten) met de gewenste attributen, bijvoorbeeld '["bsn"]'
    Possible values     Mapping: {'some_key': 'Some value'}
    Default value       {'name': 'bsn', 'required': True}
    
    Variable            DIGID_SAML_SERVICE_DESCRIPTION
    Setting             Service-omschrijving
    Description         Een beschrijving van de service die je aanbiedt.
    Possible values     string
    Default value       No default
    
    Variable            DIGID_SAML_SERVICE_NAME
    Setting             servicenaam
    Description         Naam van de service die je aanbiedt.
    Possible values     string
    Default value       No default
    
    Variable            DIGID_SAML_SIGNATURE_ALGORITHM
    Setting             signature algorithm
    Description         Ondertekenalgoritme. Merk op dat DSA_SHA1 en RSA_SHA1 deprecated zijn, maar RSA_SHA1 is nog steeds de default-waarde ind e SAMLv2-standaard. Opgelet: er zijn bekende problemen met de single-logoutfunctionaliteit indien je een ander algoritme dan SHA1 gebruikt (door hardcoded algoritmes).
    Possible values     http://www.w3.org/2000/09/xmldsig#dsa-sha1, http://www.w3.org/2000/09/xmldsig#rsa-sha1, http://www.w3.org/2001/04/xmldsig-more#rsa-sha256, http://www.w3.org/2001/04/xmldsig-more#rsa-sha384, http://www.w3.org/2001/04/xmldsig-more#rsa-sha512
    Default value       http://www.w3.org/2000/09/xmldsig#rsa-sha1
    
    Variable            DIGID_SAML_SLO
    Setting             Single logout
    Description         Single Logout is beschikbaar indien ingeschakeld
    Possible values     True, False
    Default value       True
    
    Variable            DIGID_SAML_TECHNICAL_CONTACT_PERSON_EMAIL
    Setting             technisch contactpersoon: e-mailadres
    Description         E-mailadres van de technische contactpersoon voor deze DigiD/eHerkenning/eIDAS-installatie. Je moet ook het telefoonnummer opgeven voor dit in de metadata beschikbaar is.
    Possible values     string
    Default value       No default
    
    Variable            DIGID_SAML_TECHNICAL_CONTACT_PERSON_TELEPHONE
    Setting             technisch contactpersoon: telefoonnummer
    Description         Telefoonnummer van de technische contactpersoon voor deze DigiD/eHerkenning/eIDAS-installatie. Je moet ook het e-mailadres opgeven voor dit in de metadata beschikbaar is.
    Possible values     string
    Default value       No default
    
    Variable            DIGID_SAML_WANT_ASSERTIONS_ENCRYPTED
    Setting             versleutel assertions
    Description         Indien aangevinkt, dan moeten de XML-assertions versleuteld zijn.
    Possible values     True, False
    Default value       False
    
    Variable            DIGID_SAML_WANT_ASSERTIONS_SIGNED
    Setting             onderteken assertions
    Description         Indien aangevinkt, dan moeten de XML-assertions ondertekend zijn. In het andere geval moet de hele response ondertekend zijn.
    Possible values     True, False
    Default value       True
