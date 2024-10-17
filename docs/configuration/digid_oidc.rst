.. _digid_oidc:

==========================================
Configuration for DigiD via OpenID Connect
==========================================

Settings Overview
=================


Enable/Disable configuration:
"""""""""""""""""""""""""""""

::

    DIGID_OIDC_CONFIG_ENABLE



Required:
"""""""""

::

    DIGID_OIDC_OIDC_RP_CLIENT_ID
    DIGID_OIDC_OIDC_RP_CLIENT_SECRET


All settings:
"""""""""""""

::

    DIGID_OIDC_BSN_CLAIM
    DIGID_OIDC_ENABLED
    DIGID_OIDC_OIDC_KEYCLOAK_IDP_HINT
    DIGID_OIDC_OIDC_NONCE_SIZE
    DIGID_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT
    DIGID_OIDC_OIDC_OP_DISCOVERY_ENDPOINT
    DIGID_OIDC_OIDC_OP_JWKS_ENDPOINT
    DIGID_OIDC_OIDC_OP_LOGOUT_ENDPOINT
    DIGID_OIDC_OIDC_OP_TOKEN_ENDPOINT
    DIGID_OIDC_OIDC_OP_USER_ENDPOINT
    DIGID_OIDC_OIDC_RP_CLIENT_ID
    DIGID_OIDC_OIDC_RP_CLIENT_SECRET
    DIGID_OIDC_OIDC_RP_IDP_SIGN_KEY
    DIGID_OIDC_OIDC_RP_SCOPES_LIST
    DIGID_OIDC_OIDC_RP_SIGN_ALGO
    DIGID_OIDC_OIDC_STATE_SIZE
    DIGID_OIDC_OIDC_USE_NONCE
    DIGID_OIDC_USERINFO_CLAIMS_SOURCE

Detailed Information
====================

::

    Variable            DIGID_OIDC_BSN_CLAIM
    Setting             BSN-claim
    Description         Naam van de claim die het BSN bevat van de ingelogde gebruiker.
    Possible values     No information available
    Default value       bsn
    
    Variable            DIGID_OIDC_ENABLED
    Setting             inschakelen
    Description         Indicates whether OpenID Connect for authentication/authorization is enabled
    Possible values     True, False
    Default value       False
    
    Variable            DIGID_OIDC_OIDC_KEYCLOAK_IDP_HINT
    Setting             Keycloak-identiteitsprovider hint
    Description         Specifiek voor Keycloak: parameter die aangeeft welke identiteitsprovider gebruikt moet worden (inlogscherm van Keycloak overslaan).
    Possible values     string
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_NONCE_SIZE
    Setting             Nonce size
    Description         Sets the length of the random string used for OpenID Connect nonce verification
    Possible values     string representing a positive integer
    Default value       32
    
    Variable            DIGID_OIDC_OIDC_OP_AUTHORIZATION_ENDPOINT
    Setting             Authorization endpoint
    Description         URL of your OpenID Connect provider authorization endpoint
    Possible values     string (URL)
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_OP_DISCOVERY_ENDPOINT
    Setting             Discovery endpoint
    Description         URL of your OpenID Connect provider discovery endpoint ending with a slash (`.well-known/...` will be added automatically). If this is provided, the remaining endpoints can be omitted, as they will be derived from this endpoint.
    Possible values     string (URL)
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_OP_JWKS_ENDPOINT
    Setting             JSON Web Key Set endpoint
    Description         URL of your OpenID Connect provider JSON Web Key Set endpoint. Required if `RS256` is used as signing algorithm.
    Possible values     string (URL)
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_OP_LOGOUT_ENDPOINT
    Setting             Endpoint uitlog
    Description         URL van het uitlog-endpoint van uw OpenID Connect Connect-provider
    Possible values     string (URL)
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_OP_TOKEN_ENDPOINT
    Setting             Token endpoint
    Description         URL of your OpenID Connect provider token endpoint
    Possible values     string (URL)
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_OP_USER_ENDPOINT
    Setting             User endpoint
    Description         URL of your OpenID Connect provider userinfo endpoint
    Possible values     string (URL)
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_RP_CLIENT_ID
    Setting             OpenID Connect client ID
    Description         OpenID Connect client ID provided by the OIDC Provider
    Possible values     string
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_RP_CLIENT_SECRET
    Setting             OpenID Connect secret
    Description         OpenID Connect secret provided by the OIDC Provider
    Possible values     string
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_RP_IDP_SIGN_KEY
    Setting             Sign key
    Description         Key the Identity Provider uses to sign ID tokens in the case of an RSA sign algorithm. Should be the signing key in PEM or DER format.
    Possible values     string
    Default value       No default
    
    Variable            DIGID_OIDC_OIDC_RP_SCOPES_LIST
    Setting             OpenID Connect scopes
    Description         OpenID Connect scopes that are requested during login. These scopes are hardcoded and must be supported by the identity provider.
    Possible values     No information available
    Default value       openid, bsn
    
    Variable            DIGID_OIDC_OIDC_RP_SIGN_ALGO
    Setting             OpenID sign algorithm
    Description         Algorithm the Identity Provider uses to sign ID tokens
    Possible values     string
    Default value       HS256
    
    Variable            DIGID_OIDC_OIDC_STATE_SIZE
    Setting             State size
    Description         Sets the length of the random string used for OpenID Connect state verification
    Possible values     string representing a positive integer
    Default value       32
    
    Variable            DIGID_OIDC_OIDC_USE_NONCE
    Setting             Use nonce
    Description         Controls whether the OpenID Connect client uses nonce verification
    Possible values     True, False
    Default value       True
    
    Variable            DIGID_OIDC_USERINFO_CLAIMS_SOURCE
    Setting             user information claims extracted from
    Description         Indicates the source from which the user information claims should be extracted.
    Possible values     userinfo_endpoint, id_token
    Default value       userinfo_endpoint
