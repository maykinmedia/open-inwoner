==================
Open Inwoner
==================

:Version: 1.0.1
:Source: https://github.com/maykinmedia/open-inwoner
:Keywords: inwoner
:PythonVersion: 3.9

|build-status| |docker| |black| |python-versions|

Platform to provide digital services to the residents.

Developed by `Maykin Media B.V.`_ for Dimpact and the `i4Sociaal`_ gemeenten:
Deventer, Enschede, Groningen, Leeuwarden, Zaanstad, Zwolle.


Introduction
============

Open Inwoner Platform is designed to help municipalities to support their residents and
to inform them about available services.

Using Open Inwoner platform administrators can easily fill in the information
about municipality products and services with the convenient WYSIWYG editor.
The users can search through the products with the power of the full-text
search and the questionnaires to access the services which are applicable and
useful in their situation.

The users can interact with each other and exchange messages and documents.
The users can create plans together to achieve their goals.

The style of the application is easily configurable: all the colors, images,
help texts and the logo can be set up and changed in the admin page.

Open Inwoner is developed in line with the `Common Ground`_ principles and provides
integration with Common Ground services such as Open Zaak and Haal Centraal.

.. _`Common Ground`: https://commonground.nl/


Documentation
=============

See ``INSTALL.rst`` for installation instructions, available settings and
commands.

License
=======

Copyright © Maykin Media, 2021 - 2022

Licensed under the EUPL_.


References
==========

* `Issues <https://github.com/maykinmedia/open-inwoner/issues>`_
* `Code <https://github.com/maykinmedia/open-inwoner>`_
* `Docker image <https://hub.docker.com/r/maykinmedia/open-inwoner>`_

.. |build-status| image:: https://github.com/maykinmedia/open-inwoner/actions/workflows/ci.yml/badge.svg?branch=develop
    :alt: Build status
    :target: https://github.com/maykinmedia/open-inwoner/actions/workflows/ci.yml

.. |black| image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :alt: Code style
    :target: https://github.com/psf/black

.. |docker| image:: https://img.shields.io/docker/v/maykinmedia/open-inwoner
    :alt: Docker image
    :target: https://hub.docker.com/r/maykinmedia/open-inwoner

.. |python-versions| image:: https://img.shields.io/badge/python-3.8%2B-blue.svg
    :alt: Supported Python version


.. _Maykin Media B.V.: https://www.maykinmedia.nl
.. _i4Sociaal: https://www.dimpact.nl/i4sociaal
.. _EUPL: LICENSE.md
