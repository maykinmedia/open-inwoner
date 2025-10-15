from django.db.utils import DatabaseError

import structlog

from .models import Synonym

logger = structlog.stdlib.get_logger(__name__)


def load_synonyms() -> list:
    """used for ES"""
    # todo should be refactored to be run after django migrations
    try:
        synonyms = [s.synonym_line() for s in Synonym.objects.all()]
    except DatabaseError as exc:
        logger.warning("Synonyms for elasticsearch were not loaded", exc_info=True)
        return []

    return synonyms
