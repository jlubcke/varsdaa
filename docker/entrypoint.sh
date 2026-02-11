#!/bin/sh
set -eu

# Only run Django management steps when we're starting a server.
case "${1:-}" in
    gunicorn|python)
        python django_site/manage.py migrate --noinput

        if [ "${DJANGO_COLLECTSTATIC:-}" = "1" ]; then
            python django_site/manage.py collectstatic --noinput
        fi
        ;;
esac

exec "$@"
