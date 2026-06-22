from opentelemetry import metrics

meter = metrics.get_meter("open_inwoner.openklant")

email_address_conflicts = meter.create_counter(
    "oip.openklant.email_address_conflicts",
    unit="{conflict}",
    description=(
        "Remote email addresses skipped during inbound OpenKlant2 sync "
        "because the address is already owned by another local user."
    ),
)

inbound_sync_address_operations = meter.create_counter(
    "oip.openklant.inbound_sync_address_operations",
    unit="{operation}",
    description=(
        "Digital address operations performed during inbound OpenKlant2 sync "
        "(update_user_from_partij). High delete or update rates may indicate "
        "remote misconfiguration or churn. "
        "Attributes: operation ('created', 'updated', 'deleted')."
    ),
)

outbound_stale_mappings = meter.create_counter(
    "oip.openklant.outbound_stale_mappings",
    unit="{mapping}",
    description=(
        "Stale local-to-remote mappings detected during outbound OpenKlant2 sync "
        "(update_partij_from_user_data): a mapping existed but the remote address "
        "returned 404, meaning remote and local diverged silently."
    ),
)

email_pushback = meter.create_counter(
    "oip.openklant.email_pushback",
    unit="{pushback}",
    description=(
        "Times the local standard email address was pushed back to the remote "
        "backend because the remote had email addresses but none marked as standard. "
        "Recurring counts suggest a misconfiguration or another client clearing the "
        "standard flag. "
        "Attributes: backend ('openklant2', 'esuite')."
    ),
)
