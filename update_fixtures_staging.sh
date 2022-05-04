#!/bin/sh
. env/bin/activate
for item in groningen leeuwarden zwolle deventer enschede zaanstad
do
  export DB_NAME="oip-staging-$item"
  python src/manage.py loaddata src/open_inwoner/conf/fixtures/django-admin-index.json --settings=open_inwoner.conf.staging
done
