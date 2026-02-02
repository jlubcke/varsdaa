import json

import pytest
from django.urls import reverse
from django.utils.http import urlencode

from varsdaa.models import Desk, Display, Floor, Office, User

pytestmark = [
    pytest.mark.django_db,
]


@pytest.fixture
def user():
    return User.objects.create(
        name="Putte Fisk",
        email="putte@fisk.com",
    )


@pytest.fixture
def desk():
    office = Office.objects.create(display_name='Office building A')
    floor = Floor.objects.create(
        display_name='Floor 1',
        office=office,
    )
    return Desk.objects.create(
        floor=floor,
    )


@pytest.fixture
def existing_display(desk):
    return Display.objects.create(
        desk=desk,
        product_name='DELL P3223QE',
        serial_number="892416844",
        alphanumeric_serial_number="8Y064P3",
    )


@pytest.fixture
def payload(user):
    return {
        "user_name": "puttefisk",
        "full_name": user.name,
        "displays": [
            {
                "product_name": "DELL P3223QE",
                "serial_number": "892416844",
                "alphanumeric_serial_number": "8Y064P3",
            }
        ],
    }


def test_register(client, user, payload, existing_display):
    result = client.post(
        reverse("report_display"),
        json.dumps(payload),
        content_type="application/json",
    )
    assert result.status_code == 200
    user.refresh_from_db()
    assert user.display_set.count() == 1
    assert user.office == existing_display.desk.floor.office
    Display.objects.all().delete()


def test_register_new(client, user, payload, desk):
    result = client.post(
        reverse("report_display"),
        json.dumps(payload),
        content_type="application/json",
    )
    assert result.status_code == 200

    url = result.json()['url']
    display_payload = payload['displays'][0]
    assert url.endswith(
        reverse(
            'register_display',
            kwargs=dict(email=user.email),
            query=display_payload,
        ),
    )

    # Load register_display form
    result = client.get(
        url
        + '&'
        + urlencode(
            dict(
                office=desk.floor.office.pk,
                floor=desk.floor.pk,
                desk=desk.pk,
            )
        )
    )
    assert result.status_code == 200

    # Submit form
    form = result.context['root'].parts.register_display
    result = client.post(
        url,
        {
            form.actions.submit.own_target_marker(): '',
            'office': desk.floor.office.pk,
            'floor': desk.floor.pk,
            'desk': desk.pk,
            **display_payload,
        },
    )
    assert result.status_code == 302

    # Validate placement
    user.refresh_from_db()
    assert user.display_set.count() == 1
    assert user.office == desk.floor.office

    Display.objects.all().delete()
