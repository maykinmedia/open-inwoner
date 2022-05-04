from elasticsearch_dsl import analyzer, token_filter

from .utils import load_synonyms

# token filters
synonym_filter = token_filter(
    "synonym_filter",
    type="synonym",
    # expand=True
    lenient=True,
    synonyms=load_synonyms(),
)
partial_filter = token_filter(
    token_filter(
        "partial_filter",
        type="edge_ngram",
        min_gram=3,
        max_gram=30,
    ),
)

# custom analyzers
synonym_analyzer = analyzer(
    "synonym_analyzer",
    type="custom",
    tokenizer="standard",
    filter=["lowercase", "stop", synonym_filter],
)
partial_analyzer = analyzer(
    "partial_analyzer",
    tokenizer="standard",
    filter=["lowercase", partial_filter],
)
