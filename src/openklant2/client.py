from typing import Any

from ape_pie import APIClient

from openklant2._resources.actor import ActorResource
from openklant2._resources.betrokkene import BetrokkeneResource
from openklant2._resources.digitaal_adres import DigitaalAdresResource
from openklant2._resources.interne_taak import InterneTaakResource
from openklant2._resources.klant_contact import KlantContactResource
from openklant2._resources.onderwerp_object import OnderwerpObjectResource
from openklant2._resources.partij import PartijResource
from openklant2._resources.partij_identificator import PartijIdentificatorResource


class OpenKlant2Client(APIClient):
    partij: PartijResource
    partij_identificator: PartijIdentificatorResource
    digitaal_adres: DigitaalAdresResource
    klant_contact: KlantContactResource
    onderwerp_object: OnderwerpObjectResource
    actor: ActorResource
    interne_taak: InterneTaakResource
    betrokkene: BetrokkeneResource

    def __init__(
        self,
        base_url: str,
        request_kwargs: dict[str, Any] | None = None,
    ):
        super().__init__(base_url=base_url, request_kwargs=request_kwargs)

        self.partij = PartijResource(self)
        self.partij_identificator = PartijIdentificatorResource(self)
        self.digitaal_adres = DigitaalAdresResource(self)
        self.klant_contact = KlantContactResource(self)
        self.onderwerp_object = OnderwerpObjectResource(self)
        self.actor = ActorResource(self)
        self.interne_taak = InterneTaakResource(self)
        self.betrokkene = BetrokkeneResource(self)
