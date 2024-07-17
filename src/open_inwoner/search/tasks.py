import logging

from django.core.management import call_command
from django.utils.translation import gettext as _

from open_inwoner.celery import app

logger = logging.getLogger(__name__)


@app.task(name=_("Rebuild search index"))
def rebuild_search_index(ignore_result=True):
    logger.info("starting rebuild_search_index() task")

    call_command("search_index", "--rebuild", "-f")

    logger.info("finished rebuild_search_index() task")
