import logging
import random
import time

from open_inwoner.celery import QueueOnce, app

logger = logging.getLogger(__name__)


@app.task(base=QueueOnce, once={"keys": []})
def dummy_random_wait_task():
    wait = random.randint(10, 20)  # nosec
    logger.info(f"dummy task start, waiting {wait}")
    time.sleep(wait)
    logger.info("dummy task done")
