.. _versioning-policy:

==================
Versioning policy
==================

Open Inwoner follows `semantic versioning
<https://semver.org/>`_ (``MAJOR.MINOR.PATCH``, e.g. ``2.4.2``). This
document describes how long a released version continues to receive
updates.

This policy applies to releases published from now on. Versions released
before this policy was introduced weren't governed by any documented
support window — see the :doc:`changelog` for the full release history.

Release cycle
-------------

The Open Inwoner release cycle is calendar-based and version numbers follow
semantic versioning.

We aim to release a new feature version every quarter. In SemVer terms,
this is typically a MINOR version. Occasionally a MAJOR version is released
which contains breaking changes that cannot be handled automatically. We
aim for at most one MAJOR version per calendar year, to minimize impact —
but this is best effort, not a hard limit. As an application rather than a
pure API, we treat "breaking" a bit more broadly than a broken contract
alone: a change that is high-effort or high-impact for our users — a
significant UI overhaul, a major dependency upgrade, a data migration that
needs extra care — can also warrant a MAJOR bump. As a result, MAJOR
versions might happen slightly more often here than they would for, say,
an API product. MINOR versions may deprecate functionality that is then
usually removed in the first MAJOR version that follows.

Next to that, we aim to publish a monthly PATCH release with bugfixes, for
all supported versions. Sometimes serious bugs are discovered and then we
will publish a hotfix release outside of the regular schedule. See
``SECURITY.rst`` in the root of the repository for the vulnerability
disclosure process.

In short: MAJOR and MINOR versions are *feature releases*, while PATCH
(and hotfix) versions are *bugfix releases*. The support policy below
determines how long each release keeps receiving updates.

Support policy
--------------

.. list-table::
    :header-rows: 1
    :widths: 10 45 45

    * - Version type
      - Supported until
      - Impact
    * - MAJOR (high-impact feature release)
      - 4 months after release; if a new MAJOR version supersedes this
        line while its last MINOR is still within that 4-month term, that
        MINOR's term extends by 2 months (6 months total from its own
        release). A MAJOR released after the last MINOR has already gone
        EOL does not revive it.
      - Upgrade before this term ends to stay supported
    * - MINOR (feature release)
      - 4 months after release
      - Upgrade within 4 months to stay on an actively supported MINOR
        version
    * - PATCH (bugfix release)
      - Until the next PATCH version, or until its own MINOR line's term
        ends — whichever comes first
      - Always update to the latest patch version

A few things that follow from this policy:

* Every MINOR line (e.g. ``2.3.x``) stops receiving new patches 4 months
  after its release, regardless of how many newer MINOR versions have
  shipped in the meantime — except for the last MINOR of a superseded
  MAJOR line, per the MAJOR row above.
* A specific PATCH version is by definition immediately outdated as soon as
  the next PATCH in the same line is released.

Current support status
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
    :header-rows: 1
    :widths: 10 8 14 28 12

    * - Version
      - Type
      - Release date
      - Supported until
      - Status
    * - 2.4.3
      - PATCH
      - 2026-08-11
      - Until the next PATCH version, or 2026-11-20 — whichever comes
        first
      - Active
    * - 2.4.2
      - PATCH
      - 2026-08-10
      - 2026-08-11
      - EOL
    * - 2.4.0
      - MINOR
      - 2026-07-20
      - 2026-11-20 (4 months)
      - Active

``2.4.0`` is the currently supported MINOR of the ``2.x`` line under the
plain 4-month term, since ``3.0.0`` hasn't been released. Once ``3.0.0``
is released, ``2.4.0`` — assuming no newer MINOR has replaced it by then —
becomes the last MINOR of the superseded ``2.x`` line, and its term
extends by 2 months to ``2027-01-20``.

.. note::

    Versions prior to ``2.4.x`` were not covered by this policy; see the
    :doc:`changelog` for the full release history.
