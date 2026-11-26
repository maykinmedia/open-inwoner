from opentelemetry import metrics

meter = metrics.get_meter("open_inwoner.utils")

timed_parallel_futures = meter.create_counter(
    "oip.concurrency.timed_parallel_futures",
    unit="{future}",
    description=(
        "Number of futures passed through TimedParallel.as_completed(), by "
        "outcome - recorded on every call, not just ones that hit the "
        "deadline, so a timeout rate can be computed from this alone, "
        "per call site. "
        "Attributes: outcome (str): 'completed' - finished within the "
        "budget; 'completed_late' - was still running when the deadline "
        "passed and was awaited afterwards; 'cancelled' - had not started "
        "when the deadline passed and was abandoned. "
        "name (str): identifies the TimedParallel call site."
    ),
)

timed_parallel_calls = meter.create_counter(
    "oip.concurrency.timed_parallel_calls",
    unit="{call}",
    description=(
        "Number of TimedParallel.as_completed() calls, by outcome - one "
        "event per call, not per future. This is what timed_parallel_futures "
        "can't answer on its own: a call with 1 of 10 futures cancelled and "
        "a call with 1 of 1 cancelled contribute identically to the "
        "per-future counts in aggregate, but are very different at the "
        "'did this call finish clean' level this counter tracks. "
        "Attributes: outcome (str): 'completed' - every future finished "
        "within the budget; 'timed_out' - at least one future was still "
        "outstanding when the deadline passed. "
        "name (str): identifies the TimedParallel call site."
    ),
)

cache_signature_invalid = meter.create_counter(
    "oip.cache.signature_invalid",
    unit="{value}",
    description=(
        "Number of values read from the Redis caches that were refused because "
        "they were not signed with SECRET_KEY (or one of SECRET_KEY_FALLBACKS), "
        "e.g. unsigned, tampered with or signed with another key. Refused values "
        "are never unpickled, and the read is treated as a cache miss. A spike "
        "right after rotating SECRET_KEY without a fallback is expected; otherwise "
        "it can mean that someone is writing to Redis, or that processes sharing "
        "the Redis database use different values for SECRET_KEY."
    ),
)
