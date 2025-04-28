import io
import logging

from django.core.management import call_command

from elasticsearch.exceptions import ConnectionError, ConnectionTimeout

from open_inwoner.celery import app

logger = logging.getLogger(__name__)


@app.task(
    autoretry_for=(
        ConnectionError,
        ConnectionTimeout,
    ),
    # This is a periodic job that runs nightly, and especially on test environments is
    # prone to timeouts. Hence the generous retry_backoff parameter to give us a bit of
    # slack to let the JVM garbage collector do its work.
    retry_kwargs={"max_retries": 5},
    retry_backoff=120,
    retry_jitter=True,
)
def rebuild_search_index():
    logger.info("starting rebuild_search_index() task")

    out = io.StringIO()

    call_command("search_index", "--rebuild", "-f", stdout=out)

    logger.info("finished rebuild_search_index() task")

    return out.getvalue()
