import io
import logging

from django.core.management import call_command
from django.utils.translation import gettext as _

from open_inwoner.celery import app
from open_inwoner.configurations.models import TimelineLogConfig
from open_inwoner.haalcentraal.utils import system_action

logger = logging.getLogger(__name__)


@app.task
def send_failed_mail_digest():
    logger.info("starting send_failed_mail_digest() task")

    out = io.StringIO()

    call_command("send_failed_mail_digest", stdout=out)

    logger.info("finished send_failed_mail_digest() task")

    return out.getvalue()


@app.task
def prune_timeline_logs():
    logger.info("starting prune_timeline_logs() task")

    out, err = io.StringIO(), io.StringIO()

    config = TimelineLogConfig.get_solo()
    if not config.automatically_prune_logs:
        system_action(_("aborted timeline log prune because flag is disabled"))
        return

    call_command(
        "prune_timeline_logs",
        keep_days=config.keep_days,
        stdout=out,
        stderr=err,
    )
    system_action(_("pruned timeline logs"))

    logger.info("finished prune_timeline_logs() task")

    return f"STDOUT:\n{out.getvalue()}\nSTDERR:{err.getvalue()}"
