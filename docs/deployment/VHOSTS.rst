Apache + mod-wsgi configuration
===============================

An example Apache2 vhost configuration follows::

    WSGIDaemonProcess open_inwoner-<target> threads=5 maximum-requests=1000 user=<user> group=staff
    WSGIRestrictStdout Off

    <VirtualHost *:80>
        ServerName my.domain.name

        ErrorLog "/srv/sites/open_inwoner/log/apache2/error.log"
        CustomLog "/srv/sites/open_inwoner/log/apache2/access.log" common

        WSGIProcessGroup open_inwoner-<target>

        Alias /media "/srv/sites/open_inwoner/media/"
        Alias /static "/srv/sites/open_inwoner/static/"

        WSGIScriptAlias / "/srv/sites/open_inwoner/src/open_inwoner/wsgi/wsgi_<target>.py"
    </VirtualHost>


Nginx + uwsgi + supervisor configuration
========================================

Supervisor/uwsgi:
-----------------

.. code::

    [program:uwsgi-open_inwoner-<target>]
    user = <user>
    command = /srv/sites/open_inwoner/env/bin/uwsgi --socket 127.0.0.1:8001 --wsgi-file /srv/sites/open_inwoner/src/open_inwoner/wsgi/wsgi_<target>.py
    home = /srv/sites/open_inwoner/env
    master = true
    processes = 8
    harakiri = 600
    autostart = true
    autorestart = true
    stderr_logfile = /srv/sites/open_inwoner/log/uwsgi_err.log
    stdout_logfile = /srv/sites/open_inwoner/log/uwsgi_out.log
    stopsignal = QUIT

Nginx
-----

.. code::

    upstream django_open_inwoner_<target> {
      ip_hash;
      server 127.0.0.1:8001;
    }

    server {
      listen :80;
      server_name  my.domain.name;

      access_log /srv/sites/open_inwoner/log/nginx-access.log;
      error_log /srv/sites/open_inwoner/log/nginx-error.log;

      location /500.html {
        root /srv/sites/open_inwoner/src/open_inwoner/templates/;
      }
      error_page 500 502 503 504 /500.html;

      location /static/ {
        alias /srv/sites/open_inwoner/static/;
        expires 30d;
      }

      location /media/ {
        alias /srv/sites/open_inwoner/media/;
        expires 30d;
      }

      location / {
        uwsgi_pass django_open_inwoner_<target>;
      }
    }
