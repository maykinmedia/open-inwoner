import logging

from django.core.management import call_command

from open_inwoner.celery import app

logger = logging.getLogger(__name__)


@app.task
def rebuild_search_index():
    logger.info("starting rebuild_search_index() task")

    call_command("search_index", "--rebuild", "-f")

    logger.info("finished rebuild_search_index() task")
