.. _versioning-policy:

==================
Versioning policy
==================

Open Inwoner follows `semantic versioning
<https://semver.org/>`_ (``MAJOR.MINOR.PATCH``, e.g. ``2.4.2``). This
document describes what goes into each type of release and how long a
released version continues to receive updates.

This policy applies from the ``2.4.x`` line onwards. Earlier versions
weren't governed by any documented support window --- see the
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
    high-impact for our users --- a significant UI overhaul, a major
    dependency upgrade, a non-trivial data migration that needs extra care
    --- can also warrant a MAJOR bump. Feature releases may deprecate
    functionality that is then usually removed in the first feature release
    that follows.

Bugfix release (e.g. ``2.4.1``)
    Contains fixes, small low-risk improvements, and dependency upgrades
    for which security advisories have been published, including security
    fixes. In SemVer terms this is a PATCH version. In exceptional cases,
    a high-severity issue may warrant backporting a larger change; see
    `What qualifies for a bugfix release`_.

Release calendar
----------------

Open Inwoner has a fixed release calendar:

* A new feature release is published every 4 months.
* Each feature release gets its own stable branch (``stable/X.Y.x``), from
  which the bugfix releases for that version are made.
* The most recent feature release continuously receives bug and security
  fixes, published roughly every month.
* The second-to-last feature release keeps receiving updates for at most
  8 months after its release.

When a serious bug is discovered, we may publish a hotfix release outside
of the regular schedule. See ``SECURITY.rst`` in the root of the repository
for the vulnerability disclosure process.

What qualifies for a bugfix release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following changes are typically included in a bugfix release:

* Broken functionality without a workaround: a task users would ordinarily
  expect to carry out in the application, but are unable to complete. A
  workaround may involve temporary inconvenience for existing users, or
  certain groups of users, without the issue qualifying for a bugfix
  release.
* Visual or aesthetic issues that, although not technically blocking, are
  deemed to have an adverse impact on the user experience.
* Security improvements: typically dependency updates triggered by a
  security advisory that is considered unexploitable or low-severity in the
  context of Open Inwoner. As a rule, we apply these proactively as a matter
  of good hygiene.
* Security fixes: fixes for vulnerabilities that are exploitable or of high
  severity. These are also published as bugfix releases, but follow the
  security vulnerability process described in ``SECURITY.rst`` to keep the
  issue confidential until the fix is available.
* Fixes for significant performance regressions.
* Fixes and improvements that are trivial at the code level, small in scope
  and highly unlikely to have side effects.

The following factors will typically prevent a fix from being backported to
the stable branches:

* The fix requires database migrations, in particular ones that change the
  database schema.
* The fix requires non-routine post-deployment steps, e.g. steps that
  involve follow-up actions or require judgment from the operator. Routine
  steps, such as running a script, do not by themselves prevent a fix from
  being backported.
* The fix is broad in scope or touches code with many downstream
  dependents, increasing the risk of unintended side effects. Such side
  effects are not always visible in the application itself: a change to a
  core client, for instance, may alter how API requests are built or how
  responses are handled, with consequences that depend on external systems
  and their configuration.
* The issue is a minor visual or aesthetic one, or only affects a small
  subset of users.
* The fix requires a major version upgrade of a dependency.

Fixes that are not backported on account of these factors will still be
made, but will ship in the upcoming feature release instead. These factors are always
weighed against severity, however: a security issue or high-impact bug may
still be backported if its severity warrants it.

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
      - The next feature release, but no later than 8 months after its
        own release
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
    * - 2.5.x
      - 2026-10-28
      - ---
      - Release of 2.7.0; 2027-06-28 at the latest
      - Active
    * - 2.4.x
      - 2026-07-20
      - 2.4.5
      - Release of 2.6.0; 2027-03-20 at the latest
      - Maintenance

.. note::

    Versions prior to ``2.4.x`` are not covered by this policy; see the
    :doc:`changelog` for the full release history.
