.. _eherkenning_saml:

======================================
Configuration for eHerkenning via SAML
======================================

Settings Overview
=================


Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    EHERKENNING_SAML_CONFIG_ENABLE



Required:
"""""""""

::

    EHERKENNING_SAML_BASE_URL
    EHERKENNING_SAML_CERTIFICATE_LABEL
    EHERKENNING_SAML_CERTIFICATE_PUBLIC_CERTIFICATE
    EHERKENNING_SAML_CERTIFICATE_TYPE
    EHERKENNING_SAML_ENTITY_ID
    EHERKENNING_SAML_MAKELAAR_ID
    EHERKENNING_SAML_METADATA_FILE_SOURCE
    EHERKENNING_SAML_OIN
    EHERKENNING_SAML_PRIVACY_POLICY
    EHERKENNING_SAML_SERVICE_DESCRIPTION
    EHERKENNING_SAML_SERVICE_NAME


All settings:
"""""""""""""

::

    EHERKENNING_SAML_ARTIFACT_RESOLVE_CONTENT_TYPE
    EHERKENNING_SAML_BASE_URL
    EHERKENNING_SAML_BASE_URL
    EHERKENNING_SAML_CERTIFICATE_LABEL
    EHERKENNING_SAML_CERTIFICATE_PRIVATE_KEY
    EHERKENNING_SAML_CERTIFICATE_PUBLIC_CERTIFICATE
    EHERKENNING_SAML_CERTIFICATE_TYPE
    EHERKENNING_SAML_DIGEST_ALGORITHM
    EHERKENNING_SAML_EH_ATTRIBUTE_CONSUMING_SERVICE_INDEX
    EHERKENNING_SAML_EH_LOA
    EHERKENNING_SAML_EH_REQUESTED_ATTRIBUTES
    EHERKENNING_SAML_EH_SERVICE_INSTANCE_UUID
    EHERKENNING_SAML_EH_SERVICE_UUID
    EHERKENNING_SAML_EIDAS_ATTRIBUTE_CONSUMING_SERVICE_INDEX
    EHERKENNING_SAML_EIDAS_LOA
    EHERKENNING_SAML_EIDAS_REQUESTED_ATTRIBUTES
    EHERKENNING_SAML_EIDAS_SERVICE_INSTANCE_UUID
    EHERKENNING_SAML_EIDAS_SERVICE_UUID
    EHERKENNING_SAML_ENTITY_ID
    EHERKENNING_SAML_ENTITY_ID
    EHERKENNING_SAML_KEY_PASSPHRASE
    EHERKENNING_SAML_MAKELAAR_ID
    EHERKENNING_SAML_METADATA_FILE_SOURCE
    EHERKENNING_SAML_NO_EIDAS
    EHERKENNING_SAML_OIN
    EHERKENNING_SAML_ORGANIZATION_NAME
    EHERKENNING_SAML_ORGANIZATION_URL
    EHERKENNING_SAML_PRIVACY_POLICY
    EHERKENNING_SAML_SERVICE_DESCRIPTION
    EHERKENNING_SAML_SERVICE_DESCRIPTION
    EHERKENNING_SAML_SERVICE_LANGUAGE
    EHERKENNING_SAML_SERVICE_NAME
    EHERKENNING_SAML_SERVICE_NAME
    EHERKENNING_SAML_SIGNATURE_ALGORITHM
    EHERKENNING_SAML_TECHNICAL_CONTACT_PERSON_EMAIL
    EHERKENNING_SAML_TECHNICAL_CONTACT_PERSON_TELEPHONE
    EHERKENNING_SAML_WANT_ASSERTIONS_ENCRYPTED
    EHERKENNING_SAML_WANT_ASSERTIONS_SIGNED

Detailed Information
====================

::

    Variable            EHERKENNING_SAML_ARTIFACT_RESOLVE_CONTENT_TYPE
    Setting             Content-Type 'resolve artifact binding'
    Description         'application/soap+xml' wordt als 'legacy' beschouwd. Moderne brokers verwachten typisch 'text/xml'.
    Possible values     application/soap+xml, text/xml
    Default value       application/soap+xml
    
    Variable            EHERKENNING_SAML_BASE_URL
    Setting             Basis-URL
    Description         De basis-URL van de applicatie, zonder slash op het eind.
    Possible values     string (URL)
    Default value       No default
    
    Variable            EHERKENNING_SAML_CERTIFICATE_LABEL
    Setting             label
    Description         Recognisable label for the certificate
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_CERTIFICATE_PRIVATE_KEY
    Setting             private key
    Description         The content of the private key
    Possible values     string representing the (absolute) path to a file, including file extension
    Default value       No default
    
    Variable            EHERKENNING_SAML_CERTIFICATE_PUBLIC_CERTIFICATE
    Setting             public certificate
    Description         The content of the certificate
    Possible values     string representing the (absolute) path to a file, including file extension
    Default value       No default
    
    Variable            EHERKENNING_SAML_CERTIFICATE_TYPE
    Setting             type
    Description         Is this only a certificate or is there an associated private key?
    Possible values     key_pair, cert_only
    Default value       No default
    
    Variable            EHERKENNING_SAML_DIGEST_ALGORITHM
    Setting             digest algorithm
    Description         Digest algorithm. Note that SHA1 is deprecated, but still the default value in the SAMLv2 standard. Warning: there are known issues with single-logout functionality if using anything other than SHA1 due to some hardcoded algorithm.
    Possible values     http://www.w3.org/2000/09/xmldsig#sha1, http://www.w3.org/2001/04/xmlenc#sha256, http://www.w3.org/2001/04/xmldsig-more#sha384, http://www.w3.org/2001/04/xmlenc#sha512
    Default value       http://www.w3.org/2000/09/xmldsig#sha1
    
    Variable            EHERKENNING_SAML_EH_ATTRIBUTE_CONSUMING_SERVICE_INDEX
    Setting             eHerkenning attribute consuming service index
    Description         Attribute consuming service index voor de eHerkenningservice
    Possible values     string
    Default value       9052
    
    Variable            EHERKENNING_SAML_EH_LOA
    Setting             eHerkenning LoA
    Description         Betrouwbaarheidsniveau (LoA) voor de eHerkenningservice.
    Possible values     urn:etoegang:core:assurance-class:loa1, urn:etoegang:core:assurance-class:loa2, urn:etoegang:core:assurance-class:loa2plus, urn:etoegang:core:assurance-class:loa3, urn:etoegang:core:assurance-class:loa4
    Default value       urn:etoegang:core:assurance-class:loa3
    
    Variable            EHERKENNING_SAML_EH_REQUESTED_ATTRIBUTES
    Setting             gewenste attributen
    Description         Een lijst van extra gewenste attributen. Eén enkel gewenst attribuut kan een string (de naam van het attribuut) zijn of een object met de sleutels 'name' en 'required', waarbij 'name' een string is en 'required' een boolean.
    Possible values     Mapping: {'some_key': 'Some value'}
    Default value       {'name': 'urn:etoegang:1.11:attribute-represented:CompanyName', 'required': True, 'purpose_statements': {'en': 'For testing purposes.', 'nl': 'Voor testdoeleinden.'}}
    
    Variable            EHERKENNING_SAML_EH_SERVICE_INSTANCE_UUID
    Setting             UUID eHerkenningservice instance
    Description         UUID van de eHerkenningservice-instantie. Eenmaal dit in catalogi opgenomen is kan de waarde enkel via een handmatig proces gewijzigd worden.
    Possible values     UUID string (e.g. f6b45142-0c60-4ec7-b43d-28ceacdc0b34)
    Default value       random UUID string
    
    Variable            EHERKENNING_SAML_EH_SERVICE_UUID
    Setting             UUID eHerkenningservice
    Description         UUID van de eHerkenningservice. Eenmaal dit in catalogi opgenomen is kan de waarde enkel via een handmatig proces gewijzigd worden.
    Possible values     UUID string (e.g. f6b45142-0c60-4ec7-b43d-28ceacdc0b34)
    Default value       random UUID string
    
    Variable            EHERKENNING_SAML_EIDAS_ATTRIBUTE_CONSUMING_SERVICE_INDEX
    Setting             eIDAS attribute consuming service index
    Description         Attribute consuming service index voor de eIDAS-service
    Possible values     string
    Default value       9053
    
    Variable            EHERKENNING_SAML_EIDAS_LOA
    Setting             eIDAS LoA
    Description         Betrouwbaarheidsniveau (LoA) voor de eIDAS-service.
    Possible values     urn:etoegang:core:assurance-class:loa1, urn:etoegang:core:assurance-class:loa2, urn:etoegang:core:assurance-class:loa2plus, urn:etoegang:core:assurance-class:loa3, urn:etoegang:core:assurance-class:loa4
    Default value       urn:etoegang:core:assurance-class:loa3
    
    Variable            EHERKENNING_SAML_EIDAS_REQUESTED_ATTRIBUTES
    Setting             gewenste attributen
    Description         Een lijst van extra gewenste attributen. Eén enkel gewenst attribuut kan een string (de naam van het attribuut) zijn of een object met de sleutels 'name' en 'required', waarbij 'name' een string is en 'required' een boolean.
    Possible values     Mapping: {'some_key': 'Some value'}
    Default value       {'name': 'urn:etoegang:1.9:attribute:FirstName', 'required': True, 'purpose_statements': {'en': 'For testing purposes.', 'nl': 'Voor testdoeleinden.'}}, {'name': 'urn:etoegang:1.9:attribute:FamilyName', 'required': True, 'purpose_statements': {'en': 'For testing purposes.', 'nl': 'Voor testdoeleinden.'}}, {'name': 'urn:etoegang:1.9:attribute:DateOfBirth', 'required': True, 'purpose_statements': {'en': 'For testing purposes.', 'nl': 'Voor testdoeleinden.'}}, {'name': 'urn:etoegang:1.11:attribute-represented:CompanyName', 'required': True, 'purpose_statements': {'en': 'For testing purposes.', 'nl': 'Voor testdoeleinden.'}}
    
    Variable            EHERKENNING_SAML_EIDAS_SERVICE_INSTANCE_UUID
    Setting             UUID eIDAS-service instance
    Description         UUID van de eIDAS-service-instantie. Eenmaal dit in catalogi opgenomen is kan de waarde enkel via een handmatig proces gewijzigd worden.
    Possible values     UUID string (e.g. f6b45142-0c60-4ec7-b43d-28ceacdc0b34)
    Default value       random UUID string
    
    Variable            EHERKENNING_SAML_EIDAS_SERVICE_UUID
    Setting             UUID eIDAS-service
    Description         UUID van de eIDAS-service. Eenmaal dit in catalogi opgenomen is kan de waarde enkel via een handmatig proces gewijzigd worden.
    Possible values     UUID string (e.g. f6b45142-0c60-4ec7-b43d-28ceacdc0b34)
    Default value       random UUID string
    
    Variable            EHERKENNING_SAML_ENTITY_ID
    Setting             entity ID
    Description         Service provider entity ID.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_KEY_PASSPHRASE
    Setting             wachtwoordzin private-key
    Description         Wachtwoord voor de private-key voor de authenticatie-flow.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_MAKELAAR_ID
    Setting             makelaar-ID
    Description         OIN van de makelaar waarmee eHerkenning/eIDAS ingericht is.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_METADATA_FILE_SOURCE
    Setting             (XML) metadata-URL
    Description         De URL waar het XML metadata-bestand kan gedownload worden.
    Possible values     string (URL)
    Default value       
    
    Variable            EHERKENNING_SAML_NO_EIDAS
    Setting             zonder eIDAS
    Description         Indien aangevinkt, dan zal de dienstcatalogus enkel de eHerkenningservice bevatten.
    Possible values     True, False
    Default value       False
    
    Variable            EHERKENNING_SAML_OIN
    Setting             OIN
    Description         De OIN van het bedrijf dat de service aanbiedt.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_ORGANIZATION_NAME
    Setting             organisatienaam
    Description         Naam van de organisatie die de service aanbiedt waarvoor DigiD/eHerkenning/eIDAS-authenticatie ingericht is. Je moet ook de URL opgeven voor dit in de metadata beschikbaar is.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_ORGANIZATION_URL
    Setting             organisatie-URL
    Description         URL van de organisatie die de service aanbiedt waarvoor DigiD/eHerkenning/eIDAS-authenticatie ingericht is. Je moet ook de organisatienaam opgeven voor dit in de metadata beschikbaar is.
    Possible values     string (URL)
    Default value       No default
    
    Variable            EHERKENNING_SAML_PRIVACY_POLICY
    Setting             privacybeleid
    Description         De URL waar het privacybeleid van de service-aanbieder (organisatie) beschreven staat.
    Possible values     string (URL)
    Default value       No default
    
    Variable            EHERKENNING_SAML_SERVICE_DESCRIPTION
    Setting             Service-omschrijving
    Description         Een beschrijving van de service die je aanbiedt.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_SERVICE_LANGUAGE
    Setting             servicetaal
    Description         eHerkenning/eIDAS-metadata zal deze taal bevatten
    Possible values     string
    Default value       nl
    
    Variable            EHERKENNING_SAML_SERVICE_NAME
    Setting             servicenaam
    Description         Naam van de service die je aanbiedt.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_SIGNATURE_ALGORITHM
    Setting             signature algorithm
    Description         Ondertekenalgoritme. Merk op dat DSA_SHA1 en RSA_SHA1 deprecated zijn, maar RSA_SHA1 is nog steeds de default-waarde ind e SAMLv2-standaard. Opgelet: er zijn bekende problemen met de single-logoutfunctionaliteit indien je een ander algoritme dan SHA1 gebruikt (door hardcoded algoritmes).
    Possible values     http://www.w3.org/2000/09/xmldsig#dsa-sha1, http://www.w3.org/2000/09/xmldsig#rsa-sha1, http://www.w3.org/2001/04/xmldsig-more#rsa-sha256, http://www.w3.org/2001/04/xmldsig-more#rsa-sha384, http://www.w3.org/2001/04/xmldsig-more#rsa-sha512
    Default value       http://www.w3.org/2000/09/xmldsig#rsa-sha1
    
    Variable            EHERKENNING_SAML_TECHNICAL_CONTACT_PERSON_EMAIL
    Setting             technisch contactpersoon: e-mailadres
    Description         E-mailadres van de technische contactpersoon voor deze DigiD/eHerkenning/eIDAS-installatie. Je moet ook het telefoonnummer opgeven voor dit in de metadata beschikbaar is.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_TECHNICAL_CONTACT_PERSON_TELEPHONE
    Setting             technisch contactpersoon: telefoonnummer
    Description         Telefoonnummer van de technische contactpersoon voor deze DigiD/eHerkenning/eIDAS-installatie. Je moet ook het e-mailadres opgeven voor dit in de metadata beschikbaar is.
    Possible values     string
    Default value       No default
    
    Variable            EHERKENNING_SAML_WANT_ASSERTIONS_ENCRYPTED
    Setting             versleutel assertions
    Description         Indien aangevinkt, dan moeten de XML-assertions versleuteld zijn.
    Possible values     True, False
    Default value       False
    
    Variable            EHERKENNING_SAML_WANT_ASSERTIONS_SIGNED
    Setting             onderteken assertions
    Description         Indien aangevinkt, dan moeten de XML-assertions ondertekend zijn. In het andere geval moet de hele response ondertekend zijn.
    Possible values     True, False
    Default value       True
