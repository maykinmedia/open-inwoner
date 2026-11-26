De cache voor het beperken van notificaties is altijd een Redis-cache met
dezelfde instellingen als de default cache. Alleen de locatie is nog in te stellen,
via ``CACHE_NOTIFICATION_THROTTLE_LOCATION``. De omgevingsvariabelen
``CACHE_NOTIFICATION_THROTTLE_BACKEND``,
``CACHE_NOTIFICATION_THROTTLE_CLIENT_CLASS`` en
``CACHE_NOTIFICATION_THROTTLE_IGNORE_EXCEPTIONS`` worden niet meer gebruikt:
verwijder deze uit uw configuratie. Zolang een ervan is ingesteld, geeft de
systeemcontrole bij het opstarten de waarschuwing ``utils.W002``.
