from opentelemetry import metrics

meter = metrics.get_meter("open_inwoner.cases")


case_list_views = meter.create_counter(
    "cases.list_views",
    unit="1",
    description=(
        "Number of times users view the cases list. "
        "Attributes: list_size (int), page (int)"
    ),
)

case_detail_views = meter.create_counter(
    "cases.detail_views",
    unit="1",
    description="Number of times users view case details",
)

case_document_downloads = meter.create_counter(
    "cases.document_downloads",
    unit="1",
    description="Number of times users download case documents",
)

case_document_uploads = meter.create_counter(
    "cases.document_uploads",
    unit="1",
    description="Number of times users upload documents to cases",
)

case_contact_form_registrations = meter.create_counter(
    "cases.contact_form.registrations",
    unit="1",
    description=(
        "Contact form submissions. "
        "Attributes: channel ('email' or 'api'), success (bool)"
    ),
)
