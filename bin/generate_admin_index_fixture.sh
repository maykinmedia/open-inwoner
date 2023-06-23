#!/bin/bash
#
# Dump the current (local database) admin layout to a JSON fixture. This
# overwrites the existing one.
#
# You can load this fixture with:
# $ src/manage.py loaddata django-admin-index
#
# Run this script from the root of the repository

src/manage.py dumpdata --indent=4 --natural-foreign --natural-primary admin_index.AppGroup admin_index.AppLink > src/open_inwoner/conf/fixtures/django-admin-index.json
