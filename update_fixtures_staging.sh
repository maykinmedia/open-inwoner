#!/bin/sh
. env/bin/activate
python src/manage.py loaddata src/open_inwoner/conf/fixtures/django-admin-index.json --settings=open_inwoner.conf.staging_groningen
python src/manage.py loaddata src/open_inwoner/conf/fixtures/django-admin-index.json --settings=open_inwoner.conf.staging_leeuwarden
python src/manage.py loaddata src/open_inwoner/conf/fixtures/django-admin-index.json --settings=open_inwoner.conf.staging_zwolle
python src/manage.py loaddata src/open_inwoner/conf/fixtures/django-admin-index.json --settings=open_inwoner.conf.staging_deventer
python src/manage.py loaddata src/open_inwoner/conf/fixtures/django-admin-index.json --settings=open_inwoner.conf.staging_enschede
python src/manage.py loaddata src/open_inwoner/conf/fixtures/django-admin-index.json --settings=open_inwoner.conf.staging_zaanstad
