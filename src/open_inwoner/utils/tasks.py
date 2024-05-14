import logging
import random
import time

from open_inwoner.celery import app

logger = logging.getLogger(__name__)


@app.task
def dummy_random_wait_task():
    wait = random.randint(1, 10)
    logger.info(f"dummy task start, waiting {wait}")
    time.sleep(wait)
    logger.info("dummy task done")
