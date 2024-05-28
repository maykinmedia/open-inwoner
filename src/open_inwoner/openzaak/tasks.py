import logging

from django.core.management import call_command
from django.utils.translation import gettext as _

from open_inwoner.celery import QueueOnce, app

logger = logging.getLogger(__name__)


@app.task(name=_("Import ZGW data"))
def import_zgw_data():
    logger.info("starting import_zgw_data() task")

    call_command("zgw_import_data")

    logger.info("finished import_zgw_data() task")
