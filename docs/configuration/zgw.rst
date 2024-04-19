.. _zgw:

=================
ZGW Configuration
=================

Settings Overview
=================

Required:
"""""""""

::

    ZGW_CONFIG_CATALOGI_API_CLIENT_ID
    ZGW_CONFIG_CATALOGI_API_CLIENT_SECRET
    ZGW_CONFIG_CATALOGI_API_ROOT
    ZGW_CONFIG_DOCUMENTEN_API_CLIENT_ID
    ZGW_CONFIG_DOCUMENTEN_API_CLIENT_SECRET
    ZGW_CONFIG_DOCUMENTEN_API_ROOT
    ZGW_CONFIG_FORMULIEREN_API_CLIENT_ID
    ZGW_CONFIG_FORMULIEREN_API_CLIENT_SECRET
    ZGW_CONFIG_FORMULIEREN_API_ROOT
    ZGW_CONFIG_ZAAK_API_CLIENT_ID
    ZGW_CONFIG_ZAAK_API_CLIENT_SECRET
    ZGW_CONFIG_ZAAK_API_ROOT


All settings:
"""""""""""""

::

    ZGW_CONFIG_ACTION_REQUIRED_DEADLINE_DAYS
    ZGW_CONFIG_ALLOWED_FILE_EXTENSIONS
    ZGW_CONFIG_CATALOGI_API_CLIENT_ID
    ZGW_CONFIG_CATALOGI_API_CLIENT_SECRET
    ZGW_CONFIG_CATALOGI_API_ROOT
    ZGW_CONFIG_DOCUMENTEN_API_CLIENT_ID
    ZGW_CONFIG_DOCUMENTEN_API_CLIENT_SECRET
    ZGW_CONFIG_DOCUMENTEN_API_ROOT
    ZGW_CONFIG_DOCUMENT_MAX_CONFIDENTIALITY
    ZGW_CONFIG_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN
    ZGW_CONFIG_FETCH_EHERKENNING_ZAKEN_WITH_RSIN
    ZGW_CONFIG_FORMULIEREN_API_CLIENT_ID
    ZGW_CONFIG_FORMULIEREN_API_CLIENT_SECRET
    ZGW_CONFIG_FORMULIEREN_API_ROOT
    ZGW_CONFIG_MAX_UPLOAD_SIZE
    ZGW_CONFIG_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE
    ZGW_CONFIG_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN
    ZGW_CONFIG_TITLE_TEXT
    ZGW_CONFIG_ZAAK_API_CLIENT_ID
    ZGW_CONFIG_ZAAK_API_CLIENT_SECRET
    ZGW_CONFIG_ZAAK_API_ROOT
    ZGW_CONFIG_ZAAK_MAX_CONFIDENTIALITY


Detailed Information
====================

::

    Variable            ZGW_CONFIG_ZAAK_MAX_CONFIDENTIALITY
    Setting             Zaak vertrouwelijkheid
    Description         Selecteer de maximale vertrouwelijkheid van de getoonde zaken
    Possible values     openbaar, beperkt_openbaar, intern, zaakvertrouwelijk, vertrouwelijk, confidentieel, geheim, zeer_geheim
    Default value       openbaar
    
    Variable            ZGW_CONFIG_DOCUMENT_MAX_CONFIDENTIALITY
    Setting             Documenten vertrouwelijkheid
    Description         Selecteer de maximale vertrouwelijkheid van de getoonde documenten van zaken
    Possible values     openbaar, beperkt_openbaar, intern, zaakvertrouwelijk, vertrouwelijk, confidentieel, geheim, zeer_geheim
    Default value       openbaar
    
    Variable            ZGW_CONFIG_MAX_UPLOAD_SIZE
    Setting             Maximale upload grootte (in MB)
    Description         Documentuploads mogen maximaal dit aantal MB groot zijn, anders worden ze geweigerd.
    Possible values     string representing a positive number
    Default value       50
    
    Variable            ZGW_CONFIG_ALLOWED_FILE_EXTENSIONS
    Setting             allowed file extensions
    Description         Een lijst van toegestande bestandsextensies, alleen documentuploads met een van deze extensies worden toegelaten.
    Possible values     string, comma-delimited ('foo,bar,baz')
    Default value       ['bmp', 'doc', 'docx', 'gif', 'jpeg', 'jpg', 'msg', 'pdf', 'png', 'ppt', 'pptx', 'rtf', 'tiff', 'txt', 'vsd', 'xls', 'xlsx']
    
    Variable            ZGW_CONFIG_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN
    Setting             Maak gebruik van StatusType.informeren workaround (eSuite)
    Description         Schakel dit in wanneer StatusType.informeren niet wordt ondersteund door de ZGW API waar deze omgeving aan is gekoppeld (zoals de eSuite ZGW API)Hierdoor is het verplicht om per zaaktype aan te geven wanneer een inwoner hier een notificatie van dient te krijgen.
    Possible values     True, False
    Default value       No default
    
    Variable            ZGW_CONFIG_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE
    Setting             Converteer eSuite zaaknummers
    Description         Schakel dit in om de zaaknummers van het interne eSuite format (ex: '0014ESUITE66392022') om te zetten naar een toegankelijkere notatie ('6639-2022').
    Possible values     True, False
    Default value       No default
    
    Variable            ZGW_CONFIG_FETCH_EHERKENNING_ZAKEN_WITH_RSIN
    Setting             Maak gebruik van het RSIN voor ophalen eHerkenning zaken
    Description         Indien ingeschakeld dan wordt het RSIN van eHerkenning gebruikers gebruikt om de zaken op te halen. Indien uitgeschakeld dan wordt het KVK nummer gebruikt om de zaken op te halen. Open Zaak hanteert conform de ZGW API specificatie de RSIN, de eSuite maakt gebruik van het KVK nummer.
    Possible values     True, False
    Default value       No default
    
    Variable            ZGW_CONFIG_TITLE_TEXT
    Setting             Titel tekst
    Description         De titel/introductietekst getoond op de lijstweergave van 'Mijn aanvragen'.
    Possible values     string
    Default value       Hier vindt u een overzicht van al uw lopende en afgeronde aanvragen.
    
    Variable            ZGW_CONFIG_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN
    Setting             Inschakelen gepersonaliseerde Onderwerpen op basis van zaken
    Description         Indien ingeschakeld dan worden (indien ingelogd met DigiD/eHerkenning) de getoonde onderwerpen op de Homepage bepaald op basis van de zaken van de gebruiker
    Possible values     True, False
    Default value       No default
    
    Variable            ZGW_CONFIG_ACTION_REQUIRED_DEADLINE_DAYS
    Setting             Standaard actie deadline termijn in dagen
    Description         Aantal dagen voor gebruiker om actie te ondernemen.
    Possible values     string representing a number
    Default value       15
    
    Variable            ZGW_CONFIG_CATALOGI_API_CLIENT_ID
    Setting             Client ID of the Catalogi API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CONFIG_CATALOGI_API_CLIENT_SECRET
    Setting             Client Secret of the Catalogi API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CONFIG_CATALOGI_API_ROOT
    Setting             Root URL of the Catalogi API
    Description         No description
    Possible values     string (URL)
    Default value       No default
    
    Variable            ZGW_CONFIG_DOCUMENTEN_API_CLIENT_ID
    Setting             Client ID of the Documenten API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CONFIG_DOCUMENTEN_API_CLIENT_SECRET
    Setting             Client Secret of the Documenten API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CONFIG_DOCUMENTEN_API_ROOT
    Setting             Root URL of the Documenten API
    Description         No description
    Possible values     string (URL)
    Default value       No default
    
    Variable            ZGW_CONFIG_FORMULIEREN_API_CLIENT_ID
    Setting             Client ID of the Formulieren API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CONFIG_FORMULIEREN_API_CLIENT_SECRET
    Setting             Client Secret of the Formulieren API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CONFIG_FORMULIEREN_API_ROOT
    Setting             Root URL of the Formulieren API
    Description         No description
    Possible values     string (URL)
    Default value       No default
    
    Variable            ZGW_CONFIG_ZAAK_API_CLIENT_ID
    Setting             Client ID of the Zaak API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CONFIG_ZAAK_API_CLIENT_SECRET
    Setting             Client Secret of the Zaak API
    Description         No description
    Possible values     string
    Default value       No default
    
    Variable            ZGW_CONFIG_ZAAK_API_ROOT
    Setting             Root URL of the Zaak API
    Description         No description
    Possible values     string (URL)
    Default value       No default
