import logging
from typing import Optional

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Point
from django.utils.module_loading import import_string

from furl import furl
from geopy.geocoders.base import DEFAULT_SENTINEL, Geocoder
from geopy.location import Location

logger = logging.getLogger(__name__)


class PdocLocatieserver(Geocoder):
    """
    Dutch geocoding server which uses BAG as a source.
    Documentation: https://www.pdok.nl/restful-api/-/article/pdok-locatieserver-1#
    """

    geocode_path = "/free"

    def __init__(
        self,
        *,
        timeout=DEFAULT_SENTINEL,
        proxies=DEFAULT_SENTINEL,
        domain=settings.LOCATIESERVER_DOMAIN,
        scheme="https",
        user_agent=None,
        ssl_context=DEFAULT_SENTINEL,
        adapter_factory=None
    ):
        super().__init__(
            scheme=scheme,
            timeout=timeout,
            proxies=proxies,
            user_agent=user_agent,
            ssl_context=ssl_context,
            adapter_factory=adapter_factory,
        )

        self.domain = domain.strip("/")
        self.api = "%s://%s%s" % (self.scheme, self.domain, self.geocode_path)

    def geocode(
        self,
        query,
        timeout=DEFAULT_SENTINEL,
        fq="bron:bag AND type:adres",
        ln="id,bron,weergavenaam,rdf_seealso,centroide_ll",
    ):
        """
        Return a location point by address.

        :param query: The address, query or a structured query
            you wish to geocode.

        :param int timeout: Time, in seconds, to wait for the geocoding service
            to respond before raising a :class:`geopy.exc.GeocoderTimedOut`
            exception. Set this only if you wish to override, on this call
            only, the value set during the geocoder's initialization.

        :param fq: Allows to specify a filter query, e.g. fq=bron:BAG.

        :param ln: List of fields to display
        """

        url = furl(self.api).add({"q": query, "fq": fq, "ln": ln}).url
        logger.debug("%s.geocode: %s", self.__class__.__name__, url)
        callback = self._parse_json
        return self._call_geocoder(url, callback, timeout=timeout)

    def _parse_json(self, result) -> Optional[Location]:
        if not result:
            return None

        # always return first match
        place = result["response"]["docs"][0]

        # Parse each resource.
        point = GEOSGeometry(place.get("centroide_ll"))
        placename = place.get("weergavenaam", None)
        return Location(placename, (point.y, point.x), place)


def geocode_address(address: str) -> Optional[Point]:
    geocoder_class = import_string(settings.GEOCODER)
    geocoder = geocoder_class(
        user_agent=settings.GEOPY_APP, timeout=settings.GEOPY_TIMEOUT
    )
    location = geocoder.geocode(address)
    if not location:
        return None

    coordinates = (location.longitude, location.latitude)
    return Point(coordinates)
