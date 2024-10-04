import io
import logging

from django.core.management import call_command

from open_inwoner.celery import app

logger = logging.getLogger(__name__)


@app.task
def import_product_types():
    logger.info("starting import_product_types() task")

    out = io.StringIO()

    call_command("import_product_types", stdout=out)

    logger.info("finished import_zgw_data() task")

    return out.getvalue()
