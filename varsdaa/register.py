import json

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.template import Template
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.decorators.csrf import csrf_exempt
from iommi import Asset, get_current_request
from iommi.form import choice_queryset__parse
from iommi.struct import Struct

from varsdaa.autosubmit_form import AutosubmitForm
from varsdaa.iommi import Field, Form, Page
from varsdaa.map import Map
from varsdaa.models import Desk, Display, Floor, Office, User


@csrf_exempt
def report_display(request):
    report = json.loads(request.body)

    full_name = report.get("full_name")
    user = get_object_or_404(User, name=full_name)  # @todo Take the login-with-google detour first somehow if no user

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


def register_display(request, email):
    parts = Struct()
    choose_office_form = AutosubmitForm(
        fields__office=Field.choice_queryset(choices=Office.objects.all()),
    )

    parts.choose_office = choose_office_form
    office = choose_office_form.bind(request=request).fields.office.value

    choose_floor_form = AutosubmitForm(
        editable=bool(office),
        fields__floor=Field.choice_queryset(
            choices=office.floor_set.all() if office else Floor.objects.none(),
        ),
    )
    parts.choose_floor = choose_floor_form
    floor = choose_floor_form.bind(request=request).fields.floor.value

    choose_desk_form = AutosubmitForm(
        editable=bool(office) & bool(floor),
        fields__desk=Field.choice_searchable(
            required=False,
            model=Desk,
            parse=choice_queryset__parse,
            choice_id_formatter=lambda choice, **_: choice.pk,
            choices=floor.desk_set.all() if floor else Desk.objects.none(),
        ),
        fields__map=Map(
            after=0,
            floors_all=[floor] if floor else [],
            desks_marked=floor.desk_set.all() if floor else [],
        ),
        assets__select=Asset.js(
            Template(
                # language=javascript
                """
                    window.addEventListener('DOMContentLoaded', function (event) {
                        document.querySelectorAll('.desk').forEach(
                            desk => setupSelect(desk)
                        );
                    });
                    function setupSelect(desk) {
                        desk.addEventListener('click', (event) => {
                            event.preventDefault();
                            var pk = desk.getAttribute('data-desk');
                            $('#id_desk').val(pk).trigger('change');
                        });
                    }
                """
            )
        ),
    )
    parts.choose_desk = choose_desk_form
    desk = choose_desk_form.bind(request=request).fields.desk.value

    user = get_object_or_404(User, email=email)

    def pre_save(instance, **_):
        display = instance
        display.user = user
        display.desk = desk
        display.user_updated_at = timezone.now()
        user.office = office
        user.save()

    register_display_form = Form.create(
        actions__submit__include=bool(office) & bool(floor) & bool(desk),
        title="Register display",
        model=Display,
        extra__pre_save=pre_save,
        extra__redirect=lambda form, **_: HttpResponseRedirect(user.get_absolute_url()),
        fields__product_name=Field(),
        fields__serial_number=Field(required=False),
        fields__alphanumeric_serial_number=Field(required=False),
    )
    parts.register_display = register_display_form

    return Page(parts=parts)
