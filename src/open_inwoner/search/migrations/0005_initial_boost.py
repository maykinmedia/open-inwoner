from django.db import migrations


def initiate_boost(apps, _):
    """add initial field boosts for search"""
    init_boosts = {"name": 10, "summary": 2, "content": 2, "keyword": 5}
    FieldBoost = apps.get_model("search", "FieldBoost")

    for field, boost in init_boosts.items():
        FieldBoost.objects.create(field=field, boost=boost)


class Migration(migrations.Migration):

    dependencies = [("search", "0004_fieldboost")]

    operations = [migrations.RunPython(initiate_boost, migrations.RunPython.noop)]
