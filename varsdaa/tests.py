import json

import pytest
from django.urls import reverse

from varsdaa.models import Registration
from varsdaa.models import User

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


def test_register(client, user, payload):
    result = client.post(
        reverse("report_display"),
        json.dumps(payload),
        content_type="application/json",
    )
    assert result.status_code == 200
    assert Registration.objects.filter(user=user).count() == 1
