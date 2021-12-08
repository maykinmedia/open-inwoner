import logging

from django.db.utils import DatabaseError

from .models import Synonym

logger = logging.getLogger(__name__)


def load_synonyms() -> list:
    """used for ES"""
    # todo should be refactored to be run after django migrations
    try:
        synonyms = [s.synonym_line() for s in Synonym.objects.all()]
    except DatabaseError as exc:
        logger.warning(f"Synonyms for elasticsearch were not loaded: {exc}")
        return []

    return synonyms
