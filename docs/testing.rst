.. _testing:

=======
Testing
=======

This document covers the tools to run tests and how to use them.


Django tests
============

Run the project tests by executing::

    $ python src/manage.py test src --keepdb

To measure coverage, use ``coverage run``::

    $ coverage run src/manage.py test src --keepdb

It may be convenient to add some aliases::

    $ alias runtests='python src/manage.py test --keepdb'
    $ runtests src

and::

    $ alias cov_runtests='coverage run src/manage.py test --keepdb'
    $ cov_runtests src && chromium htmlcov/index.html


OIDC login end-to-end tests
===========================

The OIDC login flows are covered by Playwright end-to-end tests
(``open_inwoner.accounts.tests.test_oidc_login_e2e``) that drive a real browser
through the full authorization-code flow against a *live* Keycloak. The
request-based OIDC tests (``test_oidc_views.py``) mock the provider's HTTP
responses, which only works for the backend's own calls; it cannot cover the
browser's navigation to Keycloak's login page, hence these separate live tests.
They are tagged ``keycloak`` (and ``e2e``) and skip themselves when Keycloak is
not reachable, so runs without it are safe.

Requirements to run locally:

* Keycloak must be reachable by BOTH the headless browser and the in-process test
  server at ``E2E_KEYCLOAK_REALM_URL`` (default: the docker dev-stack alias, with
  the ``test`` realm imported from ``docker/keycloak/fixtures/realm.json``). Bring
  it up with ``docker compose -f docker-compose.dev.yml up -d`` and ensure
  ``keycloak.open-inwoner.local`` resolves on the host (``/etc/hosts`` ->
  ``127.0.0.1``).
* The live test server binds ``localhost:8000`` because that host:port is in the
  ``testid`` client's ``redirectUris`` in the realm; Keycloak rejects any other
  callback origin. Stop the dev ``web`` container first, as it also uses ``:8000``.

Run with::

    $ python src/manage.py test src --tag=keycloak

In CI these run as part of the regular ``e2e`` job, but only on its chromium
matrix leg: that leg boots Keycloak, while the other browsers exclude the
``keycloak`` tag. The authorization-code flow relies on cross-origin cookies that
Firefox, WebKit and Edge drop by default over plain-HTTP ``localhost``, so running
it there tests browser cookie policy rather than our code.


Javascript tests
================

There are quite some options to run the Javascript tests. Karma is used as
test-runner, and you need to install it globally if you have never done so::

    $ sudo npm install -g karma

By default, the tests are run against Chrome/Chromium. To run
the tests, execute::

    $ npm test

If you want to target a single browser, you can run karma directly::

    $ karma start karma.conf.js --single-run --browsers=PhantomJS

Coverage reports can be found in ``build/reports/coverage``.

To trigger a test run on file change (source file or test file), run::

    $ karma start karma.conf.js --single-run=false --browsers=PhantomJS
