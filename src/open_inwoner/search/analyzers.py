from elasticsearch_dsl import analyzer, token_filter

from open_inwoner.synonyms.utils import load_synonyms

synonym_filter = token_filter(
    "synonym_filter",
    type="synonym",
    # expand=True  # todo discuss
    synonyms=load_synonyms(),
)

synonym_analyzer = analyzer(
    "synonym_analyzer",
    type="custom",
    tokenizer="standard",
    filter=["lowercase", "stop", synonym_filter],
)

standard_analyzer = analyzer("standard")
