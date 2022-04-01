from django.db.models.query import QuerySet


class FieldBoostQueryset(QuerySet):
    def as_dict(self) -> dict:
        return {b.field: b.boost for b in self}
