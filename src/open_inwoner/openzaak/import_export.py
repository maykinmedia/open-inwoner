import dataclasses
import io
import json
import logging
from collections import defaultdict
from typing import IO, Any, Generator, Self
from urllib.parse import urlparse

from django.core import serializers
from django.core.files.storage import Storage
from django.db import transaction
from django.db.models import QuerySet

from .models import (
    CatalogusConfig,
    ZaakTypeConfig,
    ZaakTypeInformatieObjectTypeConfig,
    ZaakTypeResultaatTypeConfig,
    ZaakTypeStatusTypeConfig,
)

logger = logging.getLogger(__name__)


@dataclasses.dataclass(frozen=True)
class CatalogusConfigExport:
    """Gather and export CatalogusConfig(s) and all associated relations."""

    catalogus_configs: QuerySet
    zaak_type_configs: QuerySet
    zaak_informatie_object_type_configs: QuerySet
    zaak_status_type_configs: QuerySet
    zaak_resultaat_type_configs: QuerySet

    def __iter__(self) -> Generator[QuerySet, Any, None]:
        yield from (
            self.catalogus_configs,
            self.zaak_type_configs,
            self.zaak_informatie_object_type_configs,
            self.zaak_status_type_configs,
            self.zaak_resultaat_type_configs,
        )

    def __eq__(self, other: QuerySet) -> bool:
        for a, b in zip(self, other):
            if a.difference(b).exists():
                return False

        return True

    @classmethod
    def from_catalogus_configs(cls, catalogus_configs: QuerySet) -> Self:
        if not isinstance(catalogus_configs, QuerySet):
            raise TypeError(
                f"`catalogus_configs` is not a QuerySet, but a {type(catalogus_configs)}"
            )

        if catalogus_configs.model != CatalogusConfig:
            raise ValueError(
                f"`catalogus_configs` is of type {catalogus_configs.model}, not CatalogusConfig"
            )

        zaak_type_configs = ZaakTypeConfig.objects.filter(
            catalogus__in=catalogus_configs
        )
        informatie_object_types = ZaakTypeInformatieObjectTypeConfig.objects.filter(
            zaaktype_config__in=zaak_type_configs
        )
        zaak_status_type_configs = ZaakTypeStatusTypeConfig.objects.filter(
            zaaktype_config__in=zaak_type_configs
        )
        zaak_resultaat_type_configs = ZaakTypeResultaatTypeConfig.objects.filter(
            zaaktype_config__in=zaak_type_configs
        )

        return cls(
            catalogus_configs=catalogus_configs,
            zaak_type_configs=zaak_type_configs,
            zaak_informatie_object_type_configs=informatie_object_types,
            zaak_status_type_configs=zaak_status_type_configs,
            zaak_resultaat_type_configs=zaak_resultaat_type_configs,
        )

    def as_dicts_iter(self) -> Generator[dict, Any, None]:
        for qs in self:
            serialized_data = serializers.serialize(
                queryset=qs,
                format="json",
                use_natural_foreign_keys=True,
                use_natural_primary_keys=True,
            )
            json_data: list[dict] = json.loads(
                serialized_data,
            )
            yield from json_data

    def as_jsonl_iter(self) -> Generator[str, Any, None]:
        for row in self.as_dicts():
            yield json.dumps(row)
            yield "\n"

    def as_dicts(self) -> list[dict]:
        return list(self.as_dicts_iter())

    def as_jsonl(self) -> str:
        return "".join(self.as_jsonl_iter())


@dataclasses.dataclass(frozen=True)
class CatalogusConfigImport:
    """Import CatalogusConfig(s) and all associated relations."""

    total_rows_processed: int = 0
    catalogus_configs_imported: int = 0
    zaaktype_configs_imported: int = 0
    zaak_inormatie_object_type_configs_imported: int = 0
    zaak_status_type_configs_imported: int = 0
    zaak_resultaat_type_configs_imported: int = 0

    @staticmethod
    def _get_url_root(url: str) -> str:
        parsed = urlparse(url)
        if not (parsed.scheme and parsed.netloc):
            raise ValueError(f"{url} is not a valid URL")

        return f"{parsed.scheme}://{parsed.netloc}"

    @classmethod
    def _lines_iter_from_jsonl_stream_or_string(
        cls, stream_or_string: IO | str
    ) -> Generator[str, Any, None]:
        lines: IO
        if isinstance(stream_or_string, str):
            lines = io.StringIO(stream_or_string)
        elif hasattr(stream_or_string, "readline"):
            lines = stream_or_string
        else:
            raise ValueError("Input must be a string stream-like object")

        for line in lines:
            if isinstance(line, bytes):  # lines might be BytesIO
                line = line.decode("utf-8")

            if not (line := line.strip()):
                continue

            yield line

        # Reset the stream in case it gets re-used
        lines.seek(0)

    @classmethod
    def _rewrite_jsonl_url_references(
        cls, stream_or_string: IO | str
    ) -> Generator[str, Any, None]:
        # The assumption is that the exporting and importing instance both have
        # a `Service` with the same slug as the `Service` referenced in the
        # `configued_from` attribute of the imported CatalogusConfig. The
        # assumption is further that all URLs in the imported objects are
        # prefixed by an URL that matches the API root in the service. Because
        # of this, the import file will contain URLs with a base URL pointing to
        # the `api_root`` of the `configured_from` Service on the _source_
        # instance, and has to be re-written to match the `api_root` of the
        # `configured_from` Service on the _target_ instance. Put differently,
        # we assume that we are migrating ZGW objects that _do not differ_ as
        # far as the ZGW objects themselves are concerned (apart from the URL,
        # they essentially point to the same ZGW backend), but that they _do_
        # differ in terms of additional model fields that do not have their
        # source of truth in the ZGW backends.
        #
        # This expectation is also encoded in our API clients: you can only
        # fetch ZGW objects using the ApePie clients if the root of those
        # objects matches the configured API root.

        base_url_mapping = {}
        for deserialized_object in serializers.deserialize(
            "jsonl",
            filter(
                lambda row: ('"model": "openzaak.catalogusconfig"' in row),
                cls._lines_iter_from_jsonl_stream_or_string(stream_or_string),
            ),
        ):
            object_type: str = deserialized_object.object.__class__.__name__

            if object_type == "CatalogusConfig":
                target_base_url = cls._get_url_root(
                    deserialized_object.object.service.api_root
                )
                source_base_url = cls._get_url_root(deserialized_object.object.url)
                base_url_mapping[source_base_url] = target_base_url
            else:
                # https://www.xkcd.com/2200/
                logger.error(
                    "Tried to filter for catalogus config objects, but also got: %s",
                    object_type,
                )

        for line in cls._lines_iter_from_jsonl_stream_or_string(stream_or_string):
            source_url_found = False
            for source, target in base_url_mapping.items():
                line = line.replace(source, target)
                source_url_found = True

            if not source_url_found:
                raise ValueError("Unable to rewrite ZGW urls")

            yield line

    @classmethod
    @transaction.atomic()
    def from_jsonl_stream_or_string(cls, stream_or_string: IO | str) -> Self:
        model_to_counter_mapping = {
            "CatalogusConfig": "catalogus_configs_imported",
            "ZaakTypeConfig": "zaaktype_configs_imported",
            "ZaakTypeInformatieObjectTypeConfig": "zaak_inormatie_object_type_configs_imported",
            "ZaakTypeStatusTypeConfig": "zaak_status_type_configs_imported",
            "ZaakTypeResultaatTypeConfig": "zaak_resultaat_type_configs_imported",
        }

        object_type_counts = defaultdict(int)

        for deserialized_object in serializers.deserialize(
            "jsonl", cls._rewrite_jsonl_url_references(stream_or_string)
        ):
            deserialized_object.save()
            object_type = deserialized_object.object.__class__.__name__
            object_type_counts[object_type] += 1

        creation_kwargs = {
            "total_rows_processed": sum(object_type_counts.values()),
        }

        for model_name, counter_field in model_to_counter_mapping.items():
            creation_kwargs[counter_field] = object_type_counts[model_name]

        return cls(**creation_kwargs)

    @classmethod
    def import_from_jsonl_file_in_django_storage(cls, file_name: str, storage: Storage):
        with storage.open(file_name) as f:
            return cls.from_jsonl_stream_or_string(f)
