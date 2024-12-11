import logging

from django.db.utils import DatabaseError
from django.utils.functional import lazy

from .models import Synonym

logger = logging.getLogger(__name__)


def load_synonyms() -> list:
    """
    Lazy load synonyms for Elasticsearch
    """

    def _load_synonyms():
        try:
            synonyms = [s.synonym_line() for s in Synonym.objects.all()]
        except DatabaseError as exc:
            logger.warning(f"Synonyms for elasticsearch were not loaded: {exc}")
            return []

        return synonyms

    return lazy(_load_synonyms)
