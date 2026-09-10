#!/usr/bin/env python3
"""Render the Docker-mode and host-mode setup-configuration files from one template.

docker/setup_configuration/data.yaml.j2 (and its openzaak_config.json.j2 fixture
template) is the single source of truth for OIP's setup_configuration data, with the
satellites' addresses as Jinja2 placeholders. This script renders it twice, once per
profile:

- The Docker profile -- Docker-internal DNS aliases like `openzaak.internal:8000` --
  into docker/setup_configuration/data.yaml and fixtures/openzaak_config.json, the
  exact paths `web-init` bind-mounts and reads (see docker-compose.yml). These are
  committed to git, like requirements/*.txt compiled from requirements/*.in: run this
  script and commit the result whenever the template changes. `bin/stack.sh up`
  reruns it on every invocation so it never drifts for anyone using that script.
- The host profile -- `localhost:<published-port>` equivalents -- into the gitignored
  docker/setup_configuration/.host/ folder, for when Open Inwoner itself runs on the
  host instead of in Docker (`bin/stack.sh up --localhost`).

Usage:
    python bin/generate_setup_configuration.py
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import StrictUndefined, Template

REPO_ROOT = Path(__file__).resolve().parent.parent
SETUP_CONFIG_DIR = REPO_ROOT / "docker" / "setup_configuration"
HOST_DIR = SETUP_CONFIG_DIR / ".host"

# (template, Docker-mode destination) pairs. The host-mode destination is always
# HOST_DIR / <same filename>.
FILES = [
    (SETUP_CONFIG_DIR / "data.yaml.j2", SETUP_CONFIG_DIR / "data.yaml"),
    (
        SETUP_CONFIG_DIR / "fixtures" / "openzaak_config.json.j2",
        SETUP_CONFIG_DIR / "fixtures" / "openzaak_config.json",
    ),
]

DOCKER_PROFILE = {
    "openzaak_host": "openzaak.internal:8000",
    "openklant_host": "openklant.internal:8000",
    "objecttypes_host": "objecttypes.internal:8000",
    "objects_host": "objects.internal:8000",
    "hc_brp_host": "hc-brp.internal:5010",
    "ssd_host": "ssd.internal",
    "clamav_host": "clamav",
    "domain": "localhost:9000",
}

# Keycloak's OIDC endpoints (keycloak.open-inwoner.local:8080) are deliberately NOT
# part of either profile -- they resolve identically in both modes (a hosts-file entry
# on the host, a matching Docker network alias in Docker), so the template leaves them
# as plain literals rather than a variable.
HOST_PROFILE = {
    "openzaak_host": "localhost:8002",
    "openklant_host": "localhost:8338",
    "objecttypes_host": "localhost:8003",
    "objects_host": "localhost:8004",
    "hc_brp_host": "localhost:5010",
    "ssd_host": "localhost:5020",
    "clamav_host": "localhost",
    "domain": "localhost:8000",
}


def assert_no_internal_leftover(text: str, dest: Path) -> None:
    # Host-mode output only: catches a new Docker service being added to the
    # template without a matching HOST_PROFILE entry. StrictUndefined only catches
    # a *misspelled* {{ variable }}, not a Docker-internal address that was left as
    # a plain literal instead of being templated -- that renders through unchanged
    # into the host output too, silently unreachable from the host.
    if ".internal" in text:
        leftover = sorted(
            {line.strip() for line in text.splitlines() if ".internal" in line}
        )
        raise SystemExit(
            f"{dest.relative_to(REPO_ROOT)}: found addresses with no host "
            f"equivalent -- add them to both profiles in {Path(__file__).name}:\n  "
            + "\n  ".join(leftover)
        )


def render(
    template_path: Path,
    dest_path: Path,
    profile: dict[str, str],
    *,
    check_no_internal: bool = False,
) -> None:
    text = template_path.read_text()
    rendered = Template(
        text, undefined=StrictUndefined, keep_trailing_newline=True
    ).render(**profile)
    if check_no_internal:
        assert_no_internal_leftover(rendered, dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(rendered)
    print(f"wrote {dest_path.relative_to(REPO_ROOT)}")


def main() -> None:
    for template, docker_dest in FILES:
        render(template, docker_dest, DOCKER_PROFILE)
        render(
            template,
            HOST_DIR / docker_dest.name,
            HOST_PROFILE,
            check_no_internal=True,
        )


if __name__ == "__main__":
    main()
