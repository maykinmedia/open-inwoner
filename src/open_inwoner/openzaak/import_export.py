import dataclasses
import io
import json
import logging
from collections import defaultdict
from typing import IO, Any, Generator, Self
from urllib.parse import urlparse

from django.apps import apps
from django.core import serializers
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.files.storage import Storage
from django.core.serializers.base import DeserializationError
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


class ZGWImportError(Exception):
    @classmethod
    def extract_error_data(
        cls, exception: Exception | None = None, jsonl: str | None = None
    ):
        data = json.loads(jsonl) if jsonl is not None else {}
        source_config = apps.get_model(data["model"])

        error_type = None
        if exception:
            exc_source = type(exception.__context__)
            if exc_source is CatalogusConfig.DoesNotExist or source_config.DoesNotExist:
                error_type = ObjectDoesNotExist
            if exc_source is source_config.MultipleObjectsReturned:
                error_type = MultipleObjectsReturned

        # metadata about source_config
        items = []
        fields = data.get("fields", None)
        if source_config is CatalogusConfig:
            items = [
                f"Domein = {fields['domein']!r}",
                f"Rsin = {fields['rsin']!r}",
            ]
        if source_config is ZaakTypeConfig:
            items = [
                f"Identificatie = {fields['identificatie']!r}",
                f"Catalogus domein = {fields['catalogus'][0]!r}",
                f"Catalogus rsin = {fields['catalogus'][1]!r}",
            ]
        if source_config in {
            ZaakTypeStatusTypeConfig,
            ZaakTypeResultaatTypeConfig,
            ZaakTypeInformatieObjectTypeConfig,
        }:
            items = [
                f"omschrijving = {fields['omschrijving']!r}",
                f"ZaakTypeConfig identificatie = {fields['zaaktype_config'][0]!r}",
            ]

        return {
            "error_type": error_type,
            "source_config_name": source_config.__name__,
            "info": ", ".join(items),
        }

    @classmethod
    def from_exception_and_jsonl(cls, jsonl: str, exception: Exception) -> Self:
        error_data = cls.extract_error_data(exception=exception, jsonl=jsonl)

        error_template = (
            "%(source_config_name)s not found in target environment: %(info)s"
        )
        if error_data["error_type"] is MultipleObjectsReturned:
            error_template = "Got multiple results for %(source_config_name)s: %(info)s"

        return cls(error_template % error_data)

    @classmethod
    def from_jsonl(cls, jsonl: str) -> Self:
        error_data = cls.extract_error_data(jsonl=jsonl)
        error_template = (
            "%(source_config_name)s was processed multiple times because it contains "
            "duplicate natural keys: %(info)s"
        )
        return cls(error_template % error_data)


def check_catalogus_config_exists(source_config: CatalogusConfig, jsonl: str):
    try:
        CatalogusConfig.objects.get_by_natural_key(
            domein=source_config.domein, rsin=source_config.rsin
        )
    except (
        CatalogusConfig.DoesNotExist,
        CatalogusConfig.MultipleObjectsReturned,
    ) as exc:
        raise ZGWImportError.from_exception_and_jsonl(exception=exc, jsonl=jsonl)


def _update_config(source, target, exclude_fields):
    for field in source._meta.fields:
        field_name = field.name

        if field_name in exclude_fields:
            continue

        val = getattr(source, field_name, None)
        setattr(target, field_name, val)
        target.save()


def _update_zaaktype_config(source_config: ZaakTypeConfig, jsonl: str):
    try:
        target = ZaakTypeConfig.objects.get_by_natural_key(
            identificatie=source_config.identificatie,
            catalogus_domein=source_config.catalogus.domein,
            catalogus_rsin=source_config.catalogus.rsin,
        )
    except (
        CatalogusConfig.DoesNotExist,
        CatalogusConfig.MultipleObjectsReturned,
        ZaakTypeConfig.DoesNotExist,
        ZaakTypeConfig.MultipleObjectsReturned,
    ) as exc:
        raise ZGWImportError.from_exception_and_jsonl(exception=exc, jsonl=jsonl)
    else:
        exclude_fields = [
            "id",
            "catalogus",
            "urls",
            "zaaktype_uuids",
        ]
        _update_config(source_config, target, exclude_fields)


def _update_nested_zgw_config(
    source_config: ZaakTypeStatusTypeConfig
    | ZaakTypeResultaatTypeConfig
    | ZaakTypeInformatieObjectTypeConfig,
    exclude_fields: list[str],
    jsonl: str,
):
    zaaktype_config_identificatie = source_config.zaaktype_config.identificatie
    catalogus_domein = source_config.zaaktype_config.catalogus.domein
    catalogus_rsin = source_config.zaaktype_config.catalogus.rsin

    try:
        target = source_config.__class__.objects.get_by_natural_key(
            omschrijving=source_config.omschrijving,
            zaaktype_config_identificatie=zaaktype_config_identificatie,
            catalogus_domein=catalogus_domein,
            catalogus_rsin=catalogus_rsin,
        )
    except (source_config.DoesNotExist, source_config.MultipleObjectsReturned) as exc:
        raise ZGWImportError.from_exception_and_jsonl(exception=exc, jsonl=jsonl)
    else:
        _update_config(source_config, target, exclude_fields)


@dataclasses.dataclass(frozen=True)
class ZGWConfigExport:
    catalogus_configs: QuerySet
    zaaktype_configs: QuerySet
    zaak_informatie_object_type_configs: QuerySet
    zaak_status_type_configs: QuerySet
    zaak_resultaat_type_configs: QuerySet

    def __iter__(self) -> Generator[QuerySet, Any, None]:
        yield from (
            self.catalogus_configs,
            self.zaaktype_configs,
            self.zaak_informatie_object_type_configs,
            self.zaak_status_type_configs,
            self.zaak_resultaat_type_configs,
        )

    def __eq__(self, other: QuerySet) -> bool:
        for a, b in zip(self, other):
            if a.difference(b).exists():
                return False
        return True

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

        zaaktype_configs = ZaakTypeConfig.objects.filter(
            catalogus__in=catalogus_configs
        )
        informatie_object_types = ZaakTypeInformatieObjectTypeConfig.objects.filter(
            zaaktype_config__in=zaaktype_configs
        )
        zaak_status_type_configs = ZaakTypeStatusTypeConfig.objects.filter(
            zaaktype_config__in=zaaktype_configs
        )
        zaak_resultaat_type_configs = ZaakTypeResultaatTypeConfig.objects.filter(
            zaaktype_config__in=zaaktype_configs
        )

        return cls(
            catalogus_configs=catalogus_configs,
            zaaktype_configs=zaaktype_configs,
            zaak_informatie_object_type_configs=informatie_object_types,
            zaak_status_type_configs=zaak_status_type_configs,
            zaak_resultaat_type_configs=zaak_resultaat_type_configs,
        )

    @classmethod
    def from_zaaktype_configs(cls, zaaktype_configs: QuerySet) -> Self:
        if not isinstance(zaaktype_configs, QuerySet):
            raise TypeError(
                f"`zaaktype_configs` is not a QuerySet, but a {type(zaaktype_configs)}"
            )

        if zaaktype_configs.model != ZaakTypeConfig:
            raise ValueError(
                f"`zaaktype_configs` is of type {zaaktype_configs.model}, not ZaakTypeConfig"
            )

        informatie_object_types = ZaakTypeInformatieObjectTypeConfig.objects.filter(
            zaaktype_config__in=zaaktype_configs
        )
        zaak_status_type_configs = ZaakTypeStatusTypeConfig.objects.filter(
            zaaktype_config__in=zaaktype_configs
        )
        zaak_resultaat_type_configs = ZaakTypeResultaatTypeConfig.objects.filter(
            zaaktype_config__in=zaaktype_configs
        )

        return cls(
            catalogus_configs=CatalogusConfig.objects.none(),
            zaaktype_configs=zaaktype_configs,
            zaak_informatie_object_type_configs=informatie_object_types,
            zaak_status_type_configs=zaak_status_type_configs,
            zaak_resultaat_type_configs=zaak_resultaat_type_configs,
        )


@dataclasses.dataclass(frozen=True)
class CatalogusConfigImport:
    """Import CatalogusConfig(s) and all associated relations."""

    total_rows_processed: int = 0
    catalogus_configs_imported: int = 0
    zaaktype_configs_imported: int = 0
    zaak_informatie_object_type_configs_imported: int = 0
    zaak_status_type_configs_imported: int = 0
    zaak_resultaat_type_configs_imported: int = 0
    import_errors: list | None = None

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
    @transaction.atomic()
    def from_jsonl_stream_or_string(cls, stream_or_string: IO | str) -> Self:
        model_to_counter_mapping = {
            "CatalogusConfig": "catalogus_configs_imported",
            "ZaakTypeConfig": "zaaktype_configs_imported",
            "ZaakTypeInformatieObjectTypeConfig": "zaak_informatie_object_type_configs_imported",
            "ZaakTypeStatusTypeConfig": "zaak_status_type_configs_imported",
            "ZaakTypeResultaatTypeConfig": "zaak_resultaat_type_configs_imported",
        }
        object_type_counts = defaultdict(int)

        rows_successfully_processed = 0
        import_errors = []
        natural_keys_seen = set()
        for line in cls._lines_iter_from_jsonl_stream_or_string(stream_or_string):
            try:
                (deserialized_object,) = serializers.deserialize(
                    "jsonl",
                    line,
                    use_natural_primary_keys=True,
                    use_natural_foreign_keys=True,
                )
            except DeserializationError as exc:
                error = ZGWImportError.from_exception_and_jsonl(
                    exception=exc, jsonl=line
                )
                logger.error(error)
                import_errors.append(error)
            else:
                source_config = deserialized_object.object
                if (natural_key := source_config.natural_key()) in natural_keys_seen:
                    import_errors.append(ZGWImportError.from_jsonl(line))
                    continue
                natural_keys_seen.add(natural_key)
                try:
                    match source_config:
                        case CatalogusConfig():
                            check_catalogus_config_exists(
                                source_config=source_config, jsonl=line
                            )
                        case ZaakTypeConfig():
                            _update_zaaktype_config(
                                source_config=source_config, jsonl=line
                            )
                        case ZaakTypeInformatieObjectTypeConfig():
                            exclude_fields = [
                                "id",
                                "zaaktype_config",
                                "zaaktype_uuids",
                                "informatieobjecttype_url",
                            ]
                            _update_nested_zgw_config(
                                source_config, exclude_fields, line
                            )
                        case ZaakTypeStatusTypeConfig():
                            exclude_fields = [
                                "id",
                                "zaaktype_config",
                                "zaaktype_uuids",
                                "statustype_url",
                            ]
                            _update_nested_zgw_config(
                                source_config, exclude_fields, line
                            )
                        case ZaakTypeResultaatTypeConfig():
                            exclude_fields = [
                                "id",
                                "zaaktype_config",
                                "zaaktype_uuids",
                                "resultaattype_url",
                            ]
                            _update_nested_zgw_config(
                                source_config, exclude_fields, line
                            )
                except ZGWImportError as exc:
                    logger.error(exc)
                    import_errors.append(exc)
                else:
                    object_type = source_config.__class__.__name__
                    object_type_counts[object_type] += 1
                    rows_successfully_processed += 1

        creation_kwargs = {
            "total_rows_processed": rows_successfully_processed + len(import_errors),
            "import_errors": import_errors,
        }

        for model_name, counter_field in model_to_counter_mapping.items():
            creation_kwargs[counter_field] = object_type_counts[model_name]

        return cls(**creation_kwargs)

    @classmethod
    def import_from_jsonl_file_in_django_storage(cls, file_name: str, storage: Storage):
        with storage.open(file_name) as f:
            return cls.from_jsonl_stream_or_string(f)
