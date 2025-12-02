from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.timezone import now
from iommi import get_current_request

from varsdaa.models import Desk, Display, User

# def report_display(request):
#     response = dict()
#     report = json.loads(request.body)
#     person, _ = Person.objects.get_or_create(
#         user_name=report["user_name"],
#         defaults={"full_name": report["full_name"]},
#     )
#
#     display_identified = False
#     for display_report in report["displays"]:
#         serial_number = display_report.get("serial_number", None)
#         alphanumeric_serial_number = display_report.get(
#             "alphanumeric_serial_number", None
#         )
#
#         # Hack to be compatible with Windows clients reporting alphanumeric_serial_number as serial_number
#         if (
#             not alphanumeric_serial_number
#             and serial_number
#             and not serial_number.isdigit()
#         ):
#             display_report["alphanumeric_serial_number"] = serial_number
#             alphanumeric_serial_number = serial_number
#             del display_report["serial_number"]
#
#         try:
#             try:
#                 display = Display.objects.get(
#                     alphanumeric_serial_number=alphanumeric_serial_number,
#                     product_name=display_report["product_name"],
#                 )
#             except Display.DoesNotExist:
#                 display = Display.objects.get(
#                     serial_number=serial_number,
#                     product_name=display_report["product_name"],
#                 )
#
#             if display.extra_display:
#                 continue
#             display_identified = True
#             display.connected = True
#             update_time = timezone.now()
#             display.connection_update_time = update_time
#             display.save()
#             if display.desk:
#                 place_person(display.desk, person, update_time)
#                 break
#             else:
#                 display.delete()
#                 response["url"] = register_display_url(display_report, report, request)
#         except Display.DoesNotExist:
#             response["url"] = register_display_url(display_report, report, request)
#         except Display.MultipleObjectsReturned:
#             pass
#
#     if not display_identified:
#         try:
#             desk = Desk.objects.get(person=person)
#             display = Display.objects.get(desk=desk)
#             display.connected = False
#             display.save()
#         except (Desk.DoesNotExist, Display.DoesNotExist):
#             pass
#
#     return JsonResponse(data=response)


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
    return request.build_absolute_uri(reverse("register_display", kwargs={'email': user.email}) + "?" + q)


def place_user(desk, user, timestamp):
    pass


# def place_person(desk, person, update_time):
#     if hasattr(desk, "person"):
#         last_person = desk.person
#         last_person.desk = None
#         last_person.room = None
#         last_person.office = None
#         last_person.save()
#     person.desk = desk
#     person.room = desk.room
#     person.office = desk.room.office
#     person.location_update_time = update_time
#     person.save()
#
#
# def register_display_url(display_report, report, request):
#     params = dict(
#         user_name=report["user_name"],
#         full_name=report["full_name"],
#         **display_report,
#     )
#     q = urlencode(params)
#     return request.build_absolute_uri(reverse("register_display") + "?" + q)


def register(user, serial_numbers):
    desk = office = None
    if serial_numbers:
        desk = guess_desk(serial_numbers)
    else:
        Registration.objects.filter(user=user).delete()

    if desk:
        desk.user = user
        desk.user_updated_at = now()
        desk.save(updated_fields=['user', 'timestamp'])

        office = desk.floor.office

    identifier = ",".join(sorted(serial_numbers))
    Registration.objects.create(user=user, identifier=identifier, desk=desk, office=office)

    if desk or not serial_numbers:
        return {}

    return {
        "url": reverse("who_details", kwargs={"email": user.email}),
    }


def guess_desk(serial_numbers):
    display = Display.objects.filter(serial_number__in=serial_numbers).first()
    if display is not None:
        return display.desk
    return None
