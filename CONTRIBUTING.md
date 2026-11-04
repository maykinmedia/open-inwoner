# Contribution guidelines

If you want to contribute, we ask you to follow these guidelines.

## Reporting bugs

If you have encountered a bug in this project, please check if an issue already
exists in the list of existing [issues][issues]. If such an issue does not
exist, you can create a [new issue][new_issue]. When writing the bug report, try
to add a clear example that shows how to reproduce said bug.

## Adding new features

Before making making changes to the code, we advise you to first check the list
of existing [issues][issues] for this project to see if an issue for the
suggested changes already exists. If such an issue does not exist, you can
create a [new issue][new_issue]. Creating an issue gives an opportunity for
other developers to give tips even before you start coding.

### Code style

To keep the code clean and readable, this project uses:

- [`ruff`](https://docs.astral.sh/ruff/) to format and clean up code (removing
  unused imports, etc.)
- [`prettier`](https://github.com/prettier/prettier) to format the JS code and
  keep diffs for pull requests small Whenever a branch is pushed or a pull
  request is made, the code will be checked in CI by the tools mentioned above,
  so make sure to install these tools and run them locally before pushing
  branches/making pull requests.

The project includes a [pre-commit](https://pre-commit.com) configuration to
automatically create a pre-commit hook to apply the expected style formatting.
After installing the dev dependencies, simply do:

```
$ pre-commit install
```

Now the various formatting hooks will be run automatically as a pre-commit hook.
You can pass `--no-verify` to `git commit` to disable these checks for a
specific commit during development (but keep in mind CI won't pass until your
code conforms).

This project aims to meet the criteria of the [Standard for Public
Code][standard_for_public_code]. Please make sure that your pull requests are
compliant, that will make the reviews quicker.

### Forking the repository

In order to implement changes to this project when you do not have rights for
this [repository][repository], you must first fork the repository. Once the
repository is forked, you can clone it to your local machine.

### Making the changes

On your local machine, create a new branch, and name it like:

- `feature/some-new-feature`, if the changes implement a new feature
- `fix/some-bug`, if the changes fix a bug
- `issue/some-issue`, for all other code changes

Once you have made changes or additions to the code, you can commit them (try to
keep the commit message descriptive but short). Commits should follow the
[Conventional Commits](https://www.conventionalcommits.org/) pattern:

```
<type>: [#issue-reference] <description>

[optional body]

[optional footer(s)]
```

Common types include `feat`, `fix`, `docs`, `style`, `refactor`, `test`, and
`chore`. If an issue already exists in the list of existing [issues][issues] for
the changes you made, be sure to reference it in the commit message, e.g.
`feat: [#1234] add new feature`, and optionally in the footer. Use imperative
mood to describe the change. It can help to think of your messages as starting
with "If applied, this commit will.." (`add new feature` instead of
`added new feature`).

#### Using Commitizen

To facilitate creating commits that comply with the conventional commit format,
you can use the [Commitizen](https://github.com/commitizen-tools/commitizen) CLI
tool. This interactive tool will guide you through creating properly formatted
commit messages.

To install Commitizen:

- **Linux**: `pip install --user commitizen` or `pipx install commitizen`
- **macOS**: `brew install commitizen` or `pip install --user commitizen`

Once installed, instead of `git commit`, use:

```
$ cz commit
```

This will interactively prompt you for the commit type, description, and other
fields to build a compliant commit message.

To demonstrate that the changes implement the new feature/fix the issue, make
sure to also add tests to the existing Django testsuite.

### Making a pull request

If all changes have been committed, you can push the branch to your fork of the
repository and create a pull request to the `main` branch of this project's
repository. Your pull request will be reviewed, if applicable, feedback will be
given and if everything is approved, it will be merged.

### Updating the changelog

In most cases, you should also document your changes in the release notes. Do
not edit `CHANGELOG.rst` directly: add a reStructuredText fragment to
`.release-notes/`, named `<issue>.<type>.rst`, for example
`.release-notes/1234.fix.rst`. The fragments are combined into the changelog
with [towncrier](https://towncrier.readthedocs.io/) when a release is made.

The easiest way to create a fragment is the interactive flow:

```bash
towncrier create
```

It asks for the issue number (`+` if there is none) and the type, and then opens
your `$EDITOR` to write the entry. You can also create the file by hand, or skip
the prompts:

```bash
towncrier create 1234.fix.rst --content "Korte beschrijving van de wijziging."
```

- **Language**: the entry should preferably be written in Dutch, though English
  is fine if you are not comfortable in Dutch. English entries will be
  translated as part of preparing the release.
- **Markup**: fragments must be reStructuredText, not Markdown. The text is
  copied as-is into `CHANGELOG.rst`, so use double backticks for code,
  `` `text <https://...>`_ `` for links and `` :gh:`1234` `` for issues. Nested
  lists and `.. code-block::` directives are allowed.
- **One change per fragment.** If a change relates to several issues, add a
  fragment with _identical_ text for each issue; towncrier merges them into a
  single entry (`[#2886, #2922]: ...`).
- **No issue**: enter `+` as the issue number in `towncrier create`, which
  generates a unique name such as `+1a2b3c4d.fix.rst`. By hand, use `+` and a
  short unique name, e.g. `+upload-logging.fix.rst`. The entry is rendered
  without an issue link.

The type determines where the entry ends up. In order of appearance:

| Type                       | Section                                                         | Use for                                                                                                                  |
| -------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `security-fix`             | Beveiligingsfixes (red box at the top)                          | Fixes for high-severity vulnerabilities; installations should upgrade urgently                                           |
| `pre-upgrade`              | Upgrade informatie → Pre-upgrade aandachtspunten                | Breaking or disruptive changes, and actions required _before_ upgrading (configuration to convert, long migrations)      |
| `post-upgrade-technisch`   | Upgrade informatie → Post-upgrade → Voor technisch beheerders   | Checks or changes for system administrators after upgrading (new env vars, CSP)                                          |
| `post-upgrade-functioneel` | Upgrade informatie → Post-upgrade → Voor functioneel beheerders | Checks for functional administrators after upgrading (content, CMS, admin)                                               |
| `deprecation`              | Upgrade informatie → Uitfaseringen                              | Changes that will be made in the next feature release                                                                    |
| `highlight`                | Belangrijkste verbeteringen                                     | Highlights of the release                                                                                                |
| `security-improvement`     | Beveiligingsverbeteringen                                       | Hardening, and precautionary upgrades for lower-severity advisories                                                      |
| `feat`                     | Nieuwe functies                                                 | New functionality                                                                                                        |
| `fix`                      | Bugfixes                                                        | Bug fixes                                                                                                                |
| `maintenance`              | Onderhoud                                                       | Changes relevant to installations that are not features or fixes, e.g. dependency updates or changes to the Docker image |

Release notes are written for the people running and managing installations.
Changes that only affect development, such as refactoring, tests, CI and
developer tooling, do not need a fragment: they are covered by the commit
messages.

A single change can need more than one fragment, e.g. a `feat` describing the
feature and a `post-upgrade-technisch` describing a new environment variable.

**Dependency bumps** (e.g. from Dependabot) go in exactly one type, the first
that applies:

1. A high or critical advisory that affects Open Inwoner: `security-fix`.
2. An advisory with a lower severity, or one that does not affect Open Inwoner
   but we upgrade to be safe: `security-improvement`. Mention the advisory and
   its severity.
3. No advisory: no fragment is needed, routine bumps are summarised in a single
   `maintenance` entry when preparing the release.

### Reviews on releases

All pull requests will be reviewed by a project member before they are merged to
a release branch.

[issues]: https://github.com/maykinmedia/open-inwoner/issues
[new_issue]: https://github.com/maykinmedia/open-inwoner/issues/new/choose
[standard_for_public_code]: https://standard.publiccode.net
[repository]: https://github.com/maykinmedia/open-inwoner
