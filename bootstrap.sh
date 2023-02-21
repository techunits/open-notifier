#!/bin/sh

# migrate database
python manage.py migrate;

# load fixtures data database
python manage.py loaddata notifier/fixtures/auth.json;
python manage.py loaddata notifier/fixtures/tenants.json;
python manage.py loaddata notifier/fixtures/configurations.json;
python manage.py loaddata notifier/fixtures/templates.json;

# migrate database
python manage.py collectstatic --noinput;

if [ "$APP_TYPE" = "celery" ]
then
    # start celery task queue worker
    celery -A notifier worker -l INFO --concurrency 2
else
    # start app service
    uwsgi --master --single-interpreter --protocol http --module notifier.wsgi:application --socket 0.0.0.0:8050 --workers 4 --max-requests=1024 --backlog 256 --harakiri=8 --vacuum --gevent 1024 --lazy
fi




