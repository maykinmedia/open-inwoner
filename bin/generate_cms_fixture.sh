# !/bin/bash
#
# Dump the current (local database) cms layout to a JSON fixture. This
# overwrites the existing one.
#
# You can load this fixture with:
# $ src/manage.py loaddata cms-pages
#
# Run this script from the root of the repository

src/manage.py dumpdata --indent=4 --natural-foreign --natural-primary cms.treenode cms.placeholder cms.page cms.title cms.cmsplugin > src/open_inwoner/conf/fixtures/cms-page.json
