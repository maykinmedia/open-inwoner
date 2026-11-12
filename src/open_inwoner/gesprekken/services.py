"""
Presentation and bookkeeping for "Mijn gesprekken" on the zaak detail page.

The Gesprekken API is the source of truth. The portal keeps only:
- a version marker per zaak (cache), bumped by the event stream, so polling clients
  can tell cheaply whether anything changed;
- when a user last saw a gesprek (GesprekGezien), for e-mail notifications.
"""

import datetime as dt
import hashlib
import time
from dataclasses import dataclass, field

from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext as _

import structlog

from open_inwoner.configurations.models import SiteConfiguration

from .client import GesprekkenAPIError, GesprekkenClient, put_bestand, uuid_from_url
from .models import GesprekGezien, MijnGesprekkenConfig

logger = structlog.stdlib.get_logger(__name__)

VERSIE_TIMEOUT = 60 * 60 * 24
# Leveringsmoment has seconds only, and a page can be rendered around the moment a
# bijdrage arrives. Registering gelezen is idempotent, so a margin is harmless.
GELEZEN_MARGE = dt.timedelta(minutes=1)

# How long a request waits for the Gesprekken API to confirm an upload
BESTAND_POGINGEN = 5
BESTAND_WACHTTIJD_SECONDEN = 1


def _versie_cache_key(zaak_url: str) -> str:
    return f"gesprekken:versie:{hashlib.sha256(zaak_url.encode()).hexdigest()}"


def get_versie(zaak_url: str) -> str:
    """The current version marker of the gesprekken of a zaak ("0" if unknown)."""
    return cache.get(_versie_cache_key(zaak_url)) or "0"


def bump_versie(zaak_url: str) -> str:
    versie = str(timezone.now().timestamp())
    cache.set(_versie_cache_key(zaak_url), versie, VERSIE_TIMEOUT)
    return versie


@dataclass
class BijlageView:
    """A bijlage, shown from its weergavegegevens: no call per bestand."""

    bestand: str
    bestandsnaam: str | None = None
    content_type: str | None = None
    bestandsomvang: int | None = None

    @property
    def file_id(self) -> str:
        return uuid_from_url(self.bestand)

    @property
    def naam(self) -> str:
        # Weergavegegevens are optional; the reference is what counts
        return self.bestandsnaam or _("Bijlage")

    @property
    def icon(self) -> str:
        if (self.content_type or "").startswith("image/"):
            return "image"
        return "insert_drive_file"


@dataclass
class BijdrageView:
    uuid: str
    tekst: str
    moment: dt.datetime | None
    is_eigen: bool
    afzender: str
    bijlagen: list[BijlageView] = field(default_factory=list)
    # An automatic reply of a system actor; shown differently and never mailed
    automatisch: bool = False


@dataclass
class GesprekView:
    uuid: str
    url: str
    onderwerp: str
    gestart_op: dt.datetime | None
    is_open: bool
    bijdragen: list[BijdrageView]
    # URL of the deelname of the user, the verzender of the user's bijdragen
    eigen_deelname: str | None


def _datetime(value: str | None) -> dt.datetime | None:
    return parse_datetime(value) if value else None


def organisatie_naam(config: MijnGesprekkenConfig) -> str:
    return config.organisatie_naam or SiteConfiguration.get_solo().name


def eigen_deelname(gesprek: dict, partij_uuid: str | None) -> str | None:
    """
    The URL of the active deelname of the user in this gesprek.

    With a known Partij it is the deelname of that Partij. Without a Klanten API
    the portal falls back to the only active partij-deelname: enough for a PoC
    where only the resident takes part on the partij side. With a Klanten API but
    no known Partij (none found, or the lookup failed) the user has no deelname
    and only reads: the deelname may belong to someone else, e.g. the resident
    when the user is a gemachtigde.
    """
    from open_inwoner.openklant.models import OpenKlant2Config

    actief = [
        d
        for d in gesprek.get("gespreksdeelnames", [])
        if d.get("type") == "partij" and not d.get("momentEindeDeelname")
    ]
    if partij_uuid:
        # The deelname refers to the Partij by URL; the portal knows its uuid
        for deelname in actief:
            if uuid_from_url(deelname.get("partij")) == partij_uuid:
                return deelname["url"]
        return None
    if OpenKlant2Config.get_solo().service:
        return None
    return actief[0]["url"] if len(actief) == 1 else None


def afzender_naam(deelname: dict, deelnames: dict[str, dict]) -> str:
    """The name of a deelnemer, with the Partij it acts for: "<naam>, namens <partij>"."""
    naam = deelname.get("naam", "")
    namens = deelname.get("namens")
    if not namens:
        return naam
    vertegenwoordigd = next(
        (d.get("naam") for d in deelnames.values() if d.get("partij") == namens), None
    )
    return _("{naam}, namens {partij}").format(
        naam=naam, partij=vertegenwoordigd or _("een andere partij")
    )


def build_gesprek_view(
    gesprek: dict, partij_uuid: str | None, config: MijnGesprekkenConfig
) -> GesprekView:
    eigen = eigen_deelname(gesprek, partij_uuid)
    deelnames = {d["url"]: d for d in gesprek.get("gespreksdeelnames", [])}
    organisatie = organisatie_naam(config)

    bijdragen = []
    for bijdrage in gesprek.get("gespreksbijdragen", []):
        verzender = deelnames.get(bijdrage.get("verzender"), {})
        is_eigen = eigen is not None and bijdrage.get("verzender") == eigen
        automatisch = bool(bijdrage.get("automatisch"))
        if is_eigen:
            afzender = ""
        elif automatisch:
            afzender = _("Automatisch bericht")
        elif verzender.get("type") == "actor":
            # Medewerkers are shown as the organisation, not by name
            afzender = organisatie
        else:
            afzender = afzender_naam(verzender, deelnames)
        bijdragen.append(
            BijdrageView(
                uuid=bijdrage["uuid"],
                tekst=bijdrage.get("tekstGespreksBijdrage", ""),
                moment=_datetime(bijdrage.get("leveringsmoment")),
                is_eigen=is_eigen,
                afzender=afzender,
                automatisch=automatisch,
                bijlagen=[
                    BijlageView(
                        bestand=b["bestand"],
                        bestandsnaam=b.get("bestandsnaam") or b.get("titel"),
                        content_type=b.get("contentType"),
                        bestandsomvang=b.get("bestandsomvang"),
                    )
                    for b in bijdrage.get("bijlagen", [])
                ],
            )
        )

    return GesprekView(
        uuid=gesprek["uuid"],
        url=gesprek["url"],
        onderwerp=gesprek.get("gespreksonderwerp", ""),
        gestart_op=_datetime(gesprek.get("aanvangsmomentGesprek")),
        is_open=not gesprek.get("momentEindeGesprek"),
        bijdragen=bijdragen,
        eigen_deelname=eigen,
    )


def fetch_gesprekken_for_zaak(client: GesprekkenClient, zaak_url: str) -> list[dict]:
    """The gesprekken of a zaak in detail (with deelnames and bijdragen)."""
    return [client.get_gesprek(g["uuid"]) for g in client.list_for_zaak(zaak_url)]


class GesprekFout(Exception):
    """An action of the user did not succeed. The message is meant for the user."""


def upload_bijlage(client: GesprekkenClient, bestand: UploadedFile) -> dict:
    """
    Uploads a file (patterns/file-upload) and returns the Bijlage for a bijdrage:
    start an upload-sessie, PUT the file to the pre-signed URL, and wait until the
    API reports the bestand as `beschikbaar`.
    """
    content_type = bestand.content_type or "application/octet-stream"
    mislukt = _("Het uploaden van de bijlage is mislukt. Probeer het later opnieuw.")
    try:
        sessie = client.create_upload_sessie(
            {
                "bestandsnaam": bestand.name,
                "bestandsomvang": bestand.size,
                "contentType": content_type,
            }
        )
        put_bestand(sessie["uploadUrl"], bestand, content_type)

        for poging in range(BESTAND_POGINGEN):
            if poging:
                time.sleep(BESTAND_WACHTTIJD_SECONDEN)
            status = client.get_bestand(sessie["fileId"]).get("status")
            if status == "beschikbaar":
                return {"bestand": sessie["bestand"]["url"]}
            if status == "geweigerd":
                raise GesprekFout(_("De bijlage is geweigerd. Kies een ander bestand."))
            if status != "uploadInAfwachting":
                break
    except GesprekkenAPIError as exc:
        logger.exception("Could not upload bijlage")
        if exc.status_code == 413:
            raise GesprekFout(_("De bijlage is te groot.")) from exc
        raise GesprekFout(mislukt) from exc

    logger.warning("Bestand not available after upload", file_id=sessie["fileId"])
    raise GesprekFout(mislukt)


def mark_seen(client: GesprekkenClient, user, gesprek: dict, view: GesprekView) -> None:
    """
    Record that the user saw the gesprek, and register 'gelezen' in the Gesprekken
    API for bijdragen of others that arrived since the previous visit (the
    medewerker sees a read receipt; the resident does not).
    """
    now = timezone.now()
    gezien, created = GesprekGezien.objects.get_or_create(
        user=user, gesprek_url=gesprek["url"], defaults={"gezien_op": now}
    )
    vorige = None if created else gezien.gezien_op

    if view.eigen_deelname:
        for bijdrage in view.bijdragen:
            if bijdrage.is_eigen:
                continue
            if vorige and bijdrage.moment and bijdrage.moment < vorige - GELEZEN_MARGE:
                continue
            try:
                client.mark_gelezen(bijdrage.uuid, view.eigen_deelname)
            except GesprekkenAPIError:
                logger.exception("Could not register gelezen", bijdrage=bijdrage.uuid)

    if not created:
        gezien.gezien_op = now
        gezien.save(update_fields=["gezien_op"])


def resident_email(user) -> str:
    """
    The e-mail address for notifications: the spec keeps contact details out of the
    gesprek, so it comes from the digitale adressen of the Partij, the standard
    address first. Without an address there (no Klanten API configured, no Partij,
    an error) the portal falls back to the address in the user's profile.
    """
    from open_inwoner.openklant.models import OpenKlant2Config
    from open_inwoner.openklant.services import OpenKlant2Service

    config = OpenKlant2Config.get_solo()
    if config.service and (partij_uuid := resolve_partij_uuid(user)):
        try:
            adressen = OpenKlant2Service(config).filter_digitale_addressen_for_partij(
                partij_uuid, soort_digital_adres="email"
            )
        except Exception:
            logger.exception("Could not retrieve digitale adressen")
        else:
            if adressen:
                adressen.sort(key=lambda adres: not adres.get("isStandaardAdres"))
                return adressen[0]["adres"]

    return user.get_contact_email()


def partij_url(partij_uuid: str) -> str:
    """Deelnames refer to the Partij by URL; the portal knows its uuid."""
    from open_inwoner.openklant.models import OpenKlant2Config

    api_root = OpenKlant2Config.get_solo().service.api_root
    return f"{api_root.rstrip('/')}/partijen/{partij_uuid}"


def resolve_partij_uuid(user) -> str | None:
    """The Partij (Klantinteracties) of the user, if a Klanten API is configured."""
    from open_inwoner.openklant.models import OpenKlant2Config
    from open_inwoner.openklant.services import OpenKlant2Service

    config = OpenKlant2Config.get_solo()
    if not config.service:
        return None
    try:
        service = OpenKlant2Service(config)
        return service.resolve_partij_uuid(
            user, lambda: service.get_partij_for_user(user)
        )
    except Exception:
        logger.exception("Could not resolve partij for user")
        return None
