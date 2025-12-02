from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from iommi import get_current_request

from varsdaa.models import Desk, Display, User


def handle_report(report):
    full_name = report.get("full_name")
    user = get_object_or_404(User, name=full_name)

    response = {}

    display_identified = False
    for display_report in report["displays"]:
        serial_number = display_report.get("serial_number", None)
        alphanumeric_serial_number = display_report.get("alphanumeric_serial_number", None)

        # Hack to be compatible with Windows clients reporting alphanumeric_serial_number as serial_number
        if not alphanumeric_serial_number and serial_number and not serial_number.isdigit():
            display_report["alphanumeric_serial_number"] = serial_number
            alphanumeric_serial_number = serial_number
            del display_report["serial_number"]

        product_name = display_report["product_name"]

        try:
            try:
                display = Display.objects.get(
                    alphanumeric_serial_number=alphanumeric_serial_number,
                    product_name=product_name,
                )
            except Display.DoesNotExist:
                display = Display.objects.get(
                    serial_number=serial_number,
                    product_name=product_name,
                )

            timestamp = timezone.now()
            display.user = user
            display.user_updated_at = timestamp
            display.save()

            if display.desk:
                user.office = display.desk.floor.office
                user.office_updated_at = timestamp
                user.save()

            display_identified = True

        except Display.DoesNotExist:
            response["url"] = register_display_url(display_report, user)
        except Display.MultipleObjectsReturned:
            pass

    if not display_identified:
        try:
            display = Display.objects.get(user=user)
            display.user = None
            display.save()
        except (Desk.DoesNotExist, Display.DoesNotExist):
            pass

    return JsonResponse(data=response)


def register_display_url(display_report, user):
    request = get_current_request()
    params = dict(
        **display_report,
    )
    q = urlencode(params)
    return request.build_absolute_uri(reverse("register_display", kwargs={"email": user.email}) + "?" + q)
