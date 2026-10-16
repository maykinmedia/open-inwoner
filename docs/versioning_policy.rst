.. _versioning-policy:

==================
Versioning policy
==================

Open Inwoner follows `semantic versioning
<https://semver.org/>`_ (``MAJOR.MINOR.PATCH``, e.g. ``2.4.2``). This
document describes what goes into each type of release and how long a
released version continues to receive updates.

This policy applies from the ``2.4.x`` line onwards. Earlier versions
weren't governed by any documented support window — see the
:doc:`changelog` for the full release history.

Release types
-------------

We make an explicit distinction between feature releases and bugfix
releases:

Feature release (e.g. ``2.4.0``)
    Contains new or changed functionality that is not (primarily) intended
    to fix a bug, finding or security issue. In SemVer terms this is
    typically a MINOR version. Occasionally a MAJOR version is released,
    which contains breaking changes that cannot be handled automatically.
    As an application rather than a pure API, we treat "breaking" a bit more
    broadly than a broken contract alone: a change that is high-effort or
    high-impact for our users — a significant UI overhaul, a major
    dependency upgrade, a data migration that needs extra care — can also
    warrant a MAJOR bump. Feature releases may deprecate functionality that
    is then usually removed in the first MAJOR version that follows.

Bugfix release (e.g. ``2.4.1``)
    Contains exclusively fixes, and package upgrades for which security
    advisories have been published. This includes security fixes. In SemVer
    terms this is a PATCH version.

Release calendar
----------------

Open Inwoner has a fixed release calendar:

* A new feature release is published every 4 months.
* Each feature release gets its own stable branch (``stable/X.Y.x``), from
  which the bugfix releases for that version are made.
* The most recent feature release continuously receives bug and security
  fixes, published roughly every month.
* The second-to-last feature release keeps receiving updates until at most
  8 months after its release.

Sometimes serious bugs are discovered, in which case we will publish a
hotfix release outside of the regular schedule. See ``SECURITY.rst`` in the
root of the repository for the vulnerability disclosure process.

Support policy
--------------

.. list-table::
    :header-rows: 1
    :widths: 20 40 40

    * - Feature release
      - Supported until
      - Impact
    * - Most recent
      - The next feature release; it then becomes the second-to-last
        feature release
      - Receives bug and security fixes roughly every month
    * - Second-to-last
      - The next feature release, and at most 8 months after its own
        release
      - Upgrade to the most recent feature release before this term ends
        to stay supported
    * - Older
      - Not supported
      - Upgrade to a supported feature release

Within a supported feature release, always update to the latest bugfix
release: a specific bugfix version is by definition outdated as soon as the
next bugfix release in the same line is published.

Current support status
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
    :header-rows: 1
    :widths: 10 14 12 30 10

    * - Version
      - Release date
      - Latest bugfix
      - Supported until
      - Status
    * - 2.4.x
      - 2026-07-20
      - 2.4.3
      - Most recent feature release; at most 2027-03-20
      - Active

.. note::

    Versions prior to ``2.4.x`` are not covered by this policy; see the
    :doc:`changelog` for the full release history.
