from typing import Annotated

from django.core.exceptions import ValidationError

from digid_eherkenning.choices import ConfigTypes
from digid_eherkenning.models import (
    ConfigCertificate,
    DigidConfiguration,
    EherkenningConfiguration,
)
from django_setup_configuration import ConfigurationModel, DjangoModelRef
from django_setup_configuration.configuration import BaseConfigurationStep
from django_setup_configuration.exceptions import ConfigurationRunFailed
from pydantic import Field
from simple_certmanager.models import Certificate

# Fields shared by the DigiD and eHerkenning/eIDAS SAML settings.
# `idp_metadata_file` and `idp_service_entity_id` are left out: they get filled
# in automatically from `metadata_file_source` when the config is saved, so
# this step doesn't set them directly.
_BASE_SAML_FIELDS = [
    "entity_id",
    "base_url",
    "service_name",
    "service_description",
    "metadata_file_source",
    "want_assertions_signed",
    "want_assertions_encrypted",
    "artifact_resolve_content_type",
    "signature_algorithm",
    "digest_algorithm",
    "technical_contact_person_telephone",
    "technical_contact_person_email",
    "administrative_contact_person_telephone",
    "administrative_contact_person_email",
    "organization_url",
    "organization_name",
]


class CertificateConfig(ConfigurationModel):
    """
    A certificate to attach to this SAML configuration.

    If a certificate with this label already exists, it is left as is and not
    overwritten. To replace it, use a new label or edit it in the admin.
    """

    label: str = DjangoModelRef(Certificate, "label")
    type: str = DjangoModelRef(Certificate, "type")
    public_certificate: Annotated[
        str,
        Field(description="Path to the PEM-encoded public certificate file."),
    ]
    private_key: Annotated[
        str | None,
        Field(
            description="Path to the PEM-encoded private key file. Required when "
            "`type` is `key_pair`."
        ),
    ] = None


class DigidSAMLConfigurationModel(ConfigurationModel):
    """Configuration for DigiD via SAML."""

    requested_attributes: list[dict] | None = DjangoModelRef(
        DigidConfiguration, "requested_attributes"
    )
    certificate: CertificateConfig | None = Field(default=None)

    class Meta:
        django_model_refs = {
            DigidConfiguration: [
                *_BASE_SAML_FIELDS,
                "attribute_consuming_service_index",
                "slo",
            ]
        }


class eHerkenningSAMLConfigurationModel(ConfigurationModel):
    """Configuration for eHerkenning/eIDAS via SAML."""

    # These UUID fields default to `uuid.uuid4` on the Django model, but once
    # entered into external catalogues, changing the value is a manual
    # process, so a step that overwrites everything on every run must never
    # invent a fresh one. Making them required (instead of falling back to a
    # DjangoModelRef-derived default) forces every run to state the same
    # value explicitly, matching a value chosen once and pinned in the YAML.
    eh_service_uuid: Annotated[
        str,
        Field(
            description="UUID of the eHerkenning service. Once entered into "
            "catalogues, changing the value is a manual process."
        ),
    ]
    eh_service_instance_uuid: Annotated[
        str,
        Field(
            description="UUID of the eHerkenning service instance. Once "
            "entered into catalogues, changing the value is a manual process."
        ),
    ]
    eidas_service_uuid: Annotated[
        str,
        Field(
            description="UUID of the eIDAS service. Once entered into "
            "catalogues, changing the value is a manual process."
        ),
    ]
    eidas_service_instance_uuid: Annotated[
        str,
        Field(
            description="UUID of the eIDAS service instance. Once entered "
            "into catalogues, changing the value is a manual process."
        ),
    ]
    eh_requested_attributes: list[dict] | None = DjangoModelRef(
        EherkenningConfiguration, "eh_requested_attributes"
    )
    eidas_requested_attributes: list[dict] | None = DjangoModelRef(
        EherkenningConfiguration, "eidas_requested_attributes"
    )
    certificate: CertificateConfig | None = Field(default=None)

    class Meta:
        django_model_refs = {
            EherkenningConfiguration: [
                *_BASE_SAML_FIELDS,
                "oin",
                "privacy_policy",
                "makelaar_id",
                "eh_loa",
                "eh_attribute_consuming_service_index",
                "eidas_loa",
                "eidas_attribute_consuming_service_index",
                "eidas_service_description",
                "no_eidas",
                "service_description_url",
                "service_language",
            ]
        }


class _BaseSAMLConfigurationStep(BaseConfigurationStep):
    """Shared logic for the DigiD and eHerkenning/eIDAS SAML steps."""

    # set on concrete subclasses
    django_config_model: type[DigidConfiguration] | type[EherkenningConfiguration]
    config_type: ConfigTypes

    def execute(
        self, model: DigidSAMLConfigurationModel | eHerkenningSAMLConfigurationModel
    ) -> None:
        config = self.django_config_model.get_solo()

        if model.certificate:
            self._configure_certificate(model.certificate)

        for field, value in model.model_dump(exclude={"certificate"}).items():
            setattr(config, field, value)

        try:
            # save() also lives here: for DigiD/eHerkenning, saving fetches
            # metadata from the identity provider, which can fail too
            config.full_clean()
            config.save()
        except ValidationError as exc:
            raise ConfigurationRunFailed(
                f"Something went wrong while saving {type(config).__name__}: {exc}"
            ) from exc

    def _configure_certificate(self, cert_config: CertificateConfig) -> None:
        certificate, created = Certificate.objects.get_or_create(
            label=cert_config.label, defaults={"type": cert_config.type}
        )

        if created:
            try:
                with open(cert_config.public_certificate, "rb") as public_cert_file:
                    certificate.public_certificate.save(
                        "public_certificate.pem", public_cert_file, save=False
                    )
                if cert_config.private_key:
                    with open(cert_config.private_key, "rb") as private_key_file:
                        certificate.private_key.save(
                            "private_key.pem", private_key_file, save=False
                        )
            except OSError as exc:
                raise ConfigurationRunFailed(
                    f"Could not read certificate file: {exc}"
                ) from exc

            try:
                certificate.full_clean()
            except ValidationError as exc:
                raise ConfigurationRunFailed(
                    f"Something went wrong while saving the certificate: {exc}"
                ) from exc

            certificate.save()

        ConfigCertificate.objects.get_or_create(
            config_type=self.config_type, certificate=certificate
        )


class DigiDSAMLConfigurationStep(_BaseSAMLConfigurationStep):
    """
    Configures DigiD login via SAML.

    Every field is overwritten on every run, using its default when the YAML
    source doesn't set it: changes made to them in the admin do not survive
    a re-run. The certificate is the exception: attach one through the
    `certificate` key the first time, and it is left alone on later runs
    (whether or not you keep repeating it in the YAML), since re-attaching
    the same certificate on every run would keep writing new files to
    storage without ever replacing the old ones. Use a new label to attach
    a different certificate.

    Setting `metadata_file_source` fetches data from the identity provider
    right away and fills in `idp_metadata_file` and `idp_service_entity_id`;
    those two fields can't be set directly.
    """

    verbose_name = "DigiD SAML configuration"
    enable_setting = "digid_saml_config_enable"
    namespace = "digid_saml_config"
    config_model = DigidSAMLConfigurationModel
    django_config_model = DigidConfiguration
    config_type = ConfigTypes.digid


class eHerkenningSAMLConfigurationStep(_BaseSAMLConfigurationStep):
    """
    Configures eHerkenning/eIDAS login via SAML.

    Every field is overwritten on every run, using its default when the YAML
    source doesn't set it: changes made to them in the admin do not survive
    a re-run. The certificate is the exception: attach one through the
    `certificate` key the first time, and it is left alone on later runs
    (whether or not you keep repeating it in the YAML), since re-attaching
    the same certificate on every run would keep writing new files to
    storage without ever replacing the old ones. Use a new label to attach
    a different certificate.

    Setting `metadata_file_source` fetches data from the identity provider
    right away and fills in `idp_metadata_file` and `idp_service_entity_id`;
    those two fields can't be set directly. The service and instance UUID
    fields (`eh_service_uuid` and friends) have no default and must always
    be set, since once entered into external catalogues, changing them is a
    manual process elsewhere -- pick a value once and keep it fixed in the
    YAML from then on.
    """

    verbose_name = "eHerkenning/eIDAS SAML configuration"
    enable_setting = "eherkenning_saml_config_enable"
    namespace = "eherkenning_saml_config"
    config_model = eHerkenningSAMLConfigurationModel
    django_config_model = EherkenningConfiguration
    config_type = ConfigTypes.eherkenning
