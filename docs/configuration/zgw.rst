.. _zgw:

======================
ZGW APIs configuration
======================

Settings Overview
=================


Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    ZGW_CONFIG_ENABLE



Required:
"""""""""

::

    ZGW_CATALOGI_SERVICE_API_ROOT
    ZGW_CATALOGI_SERVICE_CLIENT_ID
    ZGW_CATALOGI_SERVICE_SECRET
    ZGW_DOCUMENT_SERVICE_API_ROOT
    ZGW_DOCUMENT_SERVICE_CLIENT_ID
    ZGW_DOCUMENT_SERVICE_SECRET
    ZGW_FORM_SERVICE_API_ROOT
    ZGW_FORM_SERVICE_CLIENT_ID
    ZGW_FORM_SERVICE_SECRET
    ZGW_ZAAK_SERVICE_API_ROOT
    ZGW_ZAAK_SERVICE_CLIENT_ID
    ZGW_ZAAK_SERVICE_SECRET


All settings:
"""""""""""""

::

    ZGW_ACTION_REQUIRED_DEADLINE_DAYS
    ZGW_ALLOWED_FILE_EXTENSIONS
    ZGW_CATALOGI_SERVICE_API_ROOT
    ZGW_CATALOGI_SERVICE_CLIENT_ID
    ZGW_CATALOGI_SERVICE_SECRET
    ZGW_DOCUMENT_MAX_CONFIDENTIALITY
    ZGW_DOCUMENT_SERVICE_API_ROOT
    ZGW_DOCUMENT_SERVICE_CLIENT_ID
    ZGW_DOCUMENT_SERVICE_SECRET
    ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN
    ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN
    ZGW_FORM_SERVICE_API_ROOT
    ZGW_FORM_SERVICE_CLIENT_ID
    ZGW_FORM_SERVICE_SECRET
    ZGW_MAX_UPLOAD_SIZE
    ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE
    ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN
    ZGW_TITLE_TEXT
    ZGW_ZAAK_MAX_CONFIDENTIALITY
    ZGW_ZAAK_SERVICE_API_ROOT
    ZGW_ZAAK_SERVICE_CLIENT_ID
    ZGW_ZAAK_SERVICE_SECRET

Detailed Information
====================

::

    Variable            ZGW_ACTION_REQUIRED_DEADLINE_DAYS
    Setting             Standaard actie deadline termijn in dagen
    Description         Aantal dagen voor gebruiker om actie te ondernemen.
    Possible values     string representing an integer
    Default value       15
    
    Variable            ZGW_ALLOWED_FILE_EXTENSIONS
    Setting             allowed file extensions
    Description         Een lijst van toegestande bestandsextensies, alleen documentuploads met een van deze extensies worden toegelaten.
    Possible values     string, comma-delimited ('foo,bar,baz')
    Default value       bmp, doc, docx, gif, jpeg, jpg, msg, pdf, png, ppt, pptx, rtf, tiff, txt, vsd, xls, xlsx
    
    Variable            ZGW_CATALOGI_SERVICE_API_ROOT
    Setting             api root url
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CATALOGI_SERVICE_CLIENT_ID
    Setting             client id
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CATALOGI_SERVICE_SECRET
    Setting             secret
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_DOCUMENT_MAX_CONFIDENTIALITY
    Setting             Documenten vertrouwelijkheid
    Description         Selecteer de maximale vertrouwelijkheid van de getoonde documenten van zaken
    Possible values     openbaar, beperkt_openbaar, intern, zaakvertrouwelijk, vertrouwelijk, confidentieel, geheim, zeer_geheim
    Default value       openbaar
    
    Variable            ZGW_DOCUMENT_SERVICE_API_ROOT
    Setting             api root url
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_DOCUMENT_SERVICE_CLIENT_ID
    Setting             client id
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_DOCUMENT_SERVICE_SECRET
    Setting             secret
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN
    Setting             Inschakelen gepersonaliseerde Onderwerpen op basis van zaken
    Description         Indien ingeschakeld dan worden (indien ingelogd met DigiD/eHerkenning) de getoonde onderwerpen op de Homepage bepaald op basis van de zaken van de gebruiker
    Possible values     True, False
    Default value       False
    
    Variable            ZGW_FETCH_EHERKENNING_ZAKEN_WITH_RSIN
    Setting             Maak gebruik van het RSIN voor ophalen eHerkenning zaken
    Description         Indien ingeschakeld dan wordt het RSIN van eHerkenning gebruikers gebruikt om de zaken op te halen. Indien uitgeschakeld dan wordt het KVK nummer gebruikt om de zaken op te halen. Open Zaak hanteert conform de ZGW API specificatie de RSIN, de eSuite maakt gebruik van het KVK nummer.
    Possible values     True, False
    Default value       False
    
    Variable            ZGW_FORM_SERVICE_API_ROOT
    Setting             api root url
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_FORM_SERVICE_CLIENT_ID
    Setting             client id
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_FORM_SERVICE_SECRET
    Setting             secret
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_MAX_UPLOAD_SIZE
    Setting             Maximale upload grootte (in MB)
    Description         Documentuploads mogen maximaal dit aantal MB groot zijn, anders worden ze geweigerd.
    Possible values     string representing a positive integer
    Default value       50
    
    Variable            ZGW_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE
    Setting             Converteer eSuite zaaknummers
    Description         Schakel dit in om de zaaknummers van het interne eSuite format (ex: '0014ESUITE66392022') om te zetten naar een toegankelijkere notatie ('6639-2022').
    Possible values     True, False
    Default value       False
    
    Variable            ZGW_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN
    Setting             Maak gebruik van StatusType.informeren workaround (eSuite)
    Description         Schakel dit in wanneer StatusType.informeren niet wordt ondersteund door de ZGW API waar deze omgeving aan is gekoppeld (zoals de eSuite ZGW API)Hierdoor is het verplicht om per zaaktype aan te geven wanneer een inwoner hier een notificatie van dient te krijgen.
    Possible values     True, False
    Default value       False
    
    Variable            ZGW_TITLE_TEXT
    Setting             Titel tekst
    Description         De titel/introductietekst getoond op de lijstweergave van 'Mijn aanvragen'.
    Possible values     text (string)
    Default value       Hier vindt u een overzicht van al uw lopende en afgeronde aanvragen.
    
    Variable            ZGW_ZAAK_MAX_CONFIDENTIALITY
    Setting             Zaak vertrouwelijkheid
    Description         Selecteer de maximale vertrouwelijkheid van de getoonde zaken
    Possible values     openbaar, beperkt_openbaar, intern, zaakvertrouwelijk, vertrouwelijk, confidentieel, geheim, zeer_geheim
    Default value       openbaar
    
    Variable            ZGW_ZAAK_SERVICE_API_ROOT
    Setting             api root url
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_ZAAK_SERVICE_CLIENT_ID
    Setting             client id
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_ZAAK_SERVICE_SECRET
    Setting             secret
    Description         No description
    Possible values     string
    Default value       No default
