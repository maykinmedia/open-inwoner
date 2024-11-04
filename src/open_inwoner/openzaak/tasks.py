import io
import logging

from django.core.management import call_command

from open_inwoner.celery import app

logger = logging.getLogger(__name__)


@app.task
def import_zgw_data():
    logger.info("starting import_zgw_data() task")

    out = io.StringIO()

    call_command("zgw_import_data", stdout=out)

    logger.info("finished import_zgw_data() task")

    return out.getvalue()
