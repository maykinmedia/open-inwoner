.. _zgw:


=================
ZGW configuration
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
    ZGW_CONFIG_DOCUMENT_MAX_CONFIDENTIALITY
    ZGW_CONFIG_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN
    ZGW_CONFIG_FETCH_EHERKENNING_ZAKEN_WITH_RSIN
    ZGW_CONFIG_MAX_UPLOAD_SIZE
    ZGW_CONFIG_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE
    ZGW_CONFIG_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN
    ZGW_CONFIG_TITLE_TEXT
    ZGW_CONFIG_ZAAK_MAX_CONFIDENTIALITY
    


Detailed Information
====================

::

    Variable            ZGW_CONFIG_ZAAK_MAX_CONFIDENTIALITY
    Setting             Zaak vertrouwelijkheid
    Description         Selecteer de maximale vertrouwelijkheid van de getoonde zaken
    Model field type    CharField
    Possible values     string
    Default value       openbaar
    
    Variable            ZGW_CONFIG_DOCUMENT_MAX_CONFIDENTIALITY
    Setting             Documenten vertrouwelijkheid
    Description         Selecteer de maximale vertrouwelijkheid van de getoonde documenten van zaken
    Model field type    CharField
    Possible values     string
    Default value       openbaar
    
    Variable            ZGW_CONFIG_MAX_UPLOAD_SIZE
    Setting             Maximale upload grootte (in MB)
    Description         Documentuploads mogen maximaal dit aantal MB groot zijn, anders worden ze geweigerd.
    Model field type    PositiveIntegerField
    Possible values     string representing a (positive) number
    Default value       50
    
    Variable            ZGW_CONFIG_ALLOWED_FILE_EXTENSIONS
    Setting             allowed file extensions
    Description         Een lijst van toegestande bestandsextensies, alleen documentuploads met een van deze extensies worden toegelaten.
    Model field type    ArrayField
    Possible values     string, comma-delimited ('foo,bar,baz')
    Default value       No information
    
    Variable            ZGW_CONFIG_SKIP_NOTIFICATION_STATUSTYPE_INFORMEREN
    Setting             Maak gebruik van StatusType.informeren workaround (eSuite)
    Description         Schakel dit in wanneer StatusType.informeren niet wordt ondersteund door de ZGW API waar deze omgeving aan is gekoppeld (zoals de eSuite ZGW API)Hierdoor is het verplicht om per zaaktype aan te geven wanneer een inwoner hier een notificatie van dient te krijgen.
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            ZGW_CONFIG_REFORMAT_ESUITE_ZAAK_IDENTIFICATIE
    Setting             Converteer eSuite zaaknummers
    Description         Schakel dit in om de zaaknummers van het interne eSuite format (ex: '0014ESUITE66392022') om te zetten naar een toegankelijkere notatie ('6639-2022').
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            ZGW_CONFIG_FETCH_EHERKENNING_ZAKEN_WITH_RSIN
    Setting             Maak gebruik van het RSIN voor ophalen eHerkenning zaken
    Description         Indien ingeschakeld dan wordt het RSIN van eHerkenning gebruikers gebruikt om de zaken op te halen. Indien uitgeschakeld dan wordt het KVK nummer gebruikt om de zaken op te halen. Open Zaak hanteert conform de ZGW API specificatie de RSIN, de eSuite maakt gebruik van het KVK nummer.
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            ZGW_CONFIG_TITLE_TEXT
    Setting             Titel tekst
    Description         De titel/introductietekst getoond op de lijstweergave van 'Mijn aanvragen'.
    Model field type    TextField
    Possible values     string
    Default value       No information
    
    Variable            ZGW_CONFIG_ENABLE_CATEGORIES_FILTERING_WITH_ZAKEN
    Setting             Inschakelen gepersonaliseerde Onderwerpen op basis van zaken
    Description         Indien ingeschakeld dan worden (indien ingelogd met DigiD/eHerkenning) de getoonde onderwerpen op de Homepage bepaald op basis van de zaken van de gebruiker
    Model field type    BooleanField
    Possible values     True, False
    Default value       False
    
    Variable            ZGW_CONFIG_ACTION_REQUIRED_DEADLINE_DAYS
    Setting             Standaard actie deadline termijn in dagen
    Description         Aantal dagen voor gebruiker om actie te ondernemen.
    Model field type    IntegerField
    Possible values     No information available
    Default value       15
    
    