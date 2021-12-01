from .models import Synonym


def load_synonyms() -> list:
    """used for ES"""
    return [s.synonym_line() for s in Synonym.objects.all()]
