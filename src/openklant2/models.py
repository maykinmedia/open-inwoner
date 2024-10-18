from dataclasses import dataclass
from urllib.parse import urljoin


@dataclass
class OpenKlant2Config:
    api_root: str
    api_path: str
    api_token: str

    # Question/Answer settings
    mijn_vragen_kanaal: str  # e.g. "oip_mijn_vragen"
    mijn_vragen_organisatie_naam: str  # e.g. "Open Inwoner Platform",

    @property
    def api_url(self):
        return urljoin(self.api_root, self.api_path)

    @classmethod
    def from_django_settings(cls):
        from django.conf import settings

        if config := getattr(settings, "OPENKLANT2_CONFIG", None):
            return cls(**config)
