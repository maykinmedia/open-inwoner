import io

from django.core.management import call_command

import structlog

from open_inwoner.celery import app

logger = structlog.stdlib.get_logger(__name__)


@app.task
def prune_notification_records():
    logger.info("Starting prune_notification_records() task")

    out = io.StringIO()
    call_command("prune_notification_records", stdout=out)

    output = out.getvalue()
    logger.info("Finished prune_notification_records() task", output=output)

    return output
