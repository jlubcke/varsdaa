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

Client format
-------------


POST /report_display/
{
    "user_name": <user name>,
    "full_name": <full_name>,
    "displays": {
        "product_name": "DELL P3223QE",
        "serial_number": "892416844",
        "alphanumeric_serial_number": "8Y064P3"
    },
}