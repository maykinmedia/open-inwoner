from elasticsearch_dsl import analyzer, token_filter

from .utils import load_synonyms

synonym_filter = token_filter(
    "synonym_filter",
    type="synonym",
    # expand=True
    lenient=True,
    synonyms=load_synonyms(),  # todo should be refactored to be run after django migrations
)

synonym_analyzer = analyzer(
    "synonym_analyzer",
    type="custom",
    tokenizer="standard",
    filter=["lowercase", "stop", synonym_filter],
)
