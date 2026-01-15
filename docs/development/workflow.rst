Development Workflow
====================

Overview
--------

The Open Inwoner project uses **GitHub as the single source of truth** for development
work. Issues originate from multiple sources but must be converted to GitHub issues
before implementation begins.

Issue Sources
-------------

Issues come from three primary channels:

**Taiga**
  Customer support and incident response. Triaged by product owners and Maykin support
  staff. Most issues will be reported to the main open inwoner project
  (https://taiga.maykinmedia.nl/project/open-inwoner), though some issues might be
  reported in client-specific environments as well.

**Jira (Dimpact)**
  Feature specifications created and refined by product owners.

**GitHub Issue Tracker**
  Developer-driven technical improvements and issues.

.. important::
   All work destined for development must be tracked as a GitHub issue in the
   `Open Inwoner Development <https://github.com/orgs/maykinmedia/projects/20/views/>`_
   project board, regardless of origin.

   **An issue is not scheduled for work until it has been explicitly added to this
   project board.** Creating an issue in the GitHub issue tracker alone does not queue
   it for development—it must be moved to the project board during refinement or
   planning.

Workflow Stages
---------------

The project board follows a standard Kanban flow:

.. mermaid::

    graph TB
        subgraph "Issue Sources"
            H[Taiga]
            I[Jira]
            GH[GitHub Issue Tracker]
        end

        subgraph "Project Board"
            NS[No Status<br/>Refinement Queue]

            subgraph "Scheduled Work"
                TD[Todo]
                IP[In Progress]
                IR[In Review]
                DN[Done]
            end
        end

        H -.->|PO creates<br/>GitHub issue| GH
        I -.->|PO creates<br/>GitHub issue| GH

        GH -->|Anyone adds<br/>to project| NS
        H -->|Anyone adds<br/>to project| NS
        I -->|Anyone adds<br/>to project| NS

        NS -->|Approved in<br/>refinement| TD
        NS -.->|Rejected in<br/>refinement| GH

        TD --> IP
        IP --> IR
        IR --> DN

        GH -.->|External Issue URL| H
        GH -.->|External Issue URL| I

**No Status**
  Issues can be added here by anyone for discussion during refinement or weekly
  meetings. The team and PO will decide whether to schedule the issue for implementation
  and move it to the Todo column.

**Todo**
  Approved work ready to be picked up by developers.

**In Progress**
  Actively being worked on by the assigned developer.

**In Review**
  Implementation complete, awaiting code review and approval.

**Done**
  Completed and merged.

Responsibilities
----------------

Issue Creation
~~~~~~~~~~~~~~

**Product Owners**
  * Migrate features from Jira to GitHub with descriptions and acceptance criteria
  * Add issues to the development board
  * Confirm bugs and create corresponding GitHub issues

**Customer Support**
  * Work with PO to verify and confirm bugs and ensure these are pushed to the
    development board for discussion during refinement.

**Developers**
  * Create technical issues in GitHub tracker when problems are encountered
  * Issues must be approved in refinement before moving to the development board

Issue Management
~~~~~~~~~~~~~~~~

Issues must have their type and attributes set at creation or during refinement before
moving to Todo.

**Issue Types** *(set at creation/refinement)*
  * **Feature**: User-facing functionality, generally mapping to features/user stories
    from Jira
  * **Bug**: Verified defects requiring fixes
  * **Task**: Developer-driven chores, cleanups, and technical improvements
  * **Epic**: Currently not in use

**Issue Attributes** *(set at creation/refinement)*
  * **Milestone**: Issues should be assigned to one of the active milestones, virtually
    always the upcoming release
  * **External Issue URL**: Use this custom field to link back to the originating Taiga
    or Jira ticket

**Assigned Developer**
  * Move the issue through board columns
  * Create sub-issues for implementation details
  * Raise questions or mark as blocked if problems arise (use GitHub's "blocked by"
    feature to reference the blocking issue)
  * Responsible for overall issue progress

.. note::
   Assignment typically happens during weekly planning or standup meetings.

Issue Structure
---------------

**Features**
  Follow the principle: **1 Feature = 1 GitHub Issue**. Use sub-issues to organize
  implementation work and track progress.

**Technical Issues**
  The main issue captures the goal or objective. Implementation details go in sub-issues
  when needed.

Milestones and Labels
---------------------

Milestones
~~~~~~~~~~

In general, most features are scheduled for the upcoming release milestone as part of an
active sprint. In some cases, there may be overarching milestones that span multiple
sprints and releases and have their own milestone. Tag issues with the appropriate
milestone to track release scope.

Labels
~~~~~~

Labels are not officially used for project management purposes. The first-class
attributes (issue types, milestones, assignees) provide the primary organizational
structure.

However, developers are free to use their own labelling system to help track and filter
issues according to their needs.

The one exception is:

``needs-backport``
  **Special case**: This label marks issues that should be applied to an earlier release
  after completion. Mainly used for bug fixes that need to be backported to stable
  branches.
