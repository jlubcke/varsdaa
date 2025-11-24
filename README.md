Varsdå?
=======

To run:

- `uv run python example/manage.py migrate`
- `uv run python example/manage.py createsuperuser`
- `uv run python example/manage.py runserver`

To set up google, follow django-allauth instruction to get client id and client secret. Then log in as superuser and set
up a "Social application" with the values:

- Provider: `google`
- Name: `google`
- Client ID: <client_id>
- Client secret: <client_secret>
