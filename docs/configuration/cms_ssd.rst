.. _cms_ssd:

===============================================
Configuration for CMS social benefits (SSD) app
===============================================

Settings Overview
=================


Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    CMS_CONFIG_SSD_ENABLE




All settings:
"""""""""""""

::

    CMS_SSD_MENU_ICON
    CMS_SSD_MENU_INDICATOR
    CMS_SSD_REQUIRES_AUTH
    CMS_SSD_REQUIRES_AUTH_BSN_OR_KVK

Detailed Information
====================

::

    Variable            CMS_SSD_MENU_ICON
    Description         Icon in the menu
    Possible values     String
    Default value       No default
    
    Variable            CMS_SSD_MENU_INDICATOR
    Description         Menu indicator for the app
    Possible values     String
    Default value       No default
    
    Variable            CMS_SSD_REQUIRES_AUTH
    Description         Whether the access to the page is restricted
    Possible values     True, False
    Default value       No default
    
    Variable            CMS_SSD_REQUIRES_AUTH_BSN_OR_KVK
    Description         Access to the page requires BSN or KVK
    Possible values     True, False
    Default value       No default
