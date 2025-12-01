import json

from allauth.socialaccount.adapter import get_adapter
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import Template
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from iommi import LAST, Asset
from iommi import html
from iommi.form import choice_queryset__parse
from iommi.struct import Struct

from varsdaa.autosubmit_form import AutosubmitForm
from varsdaa.iommi import Column
from varsdaa.iommi import Field
from varsdaa.iommi import Form
from varsdaa.iommi import Page
from varsdaa.iommi import Table
from varsdaa.map import Map
from varsdaa.models import Desk
from varsdaa.models import Display
from varsdaa.models import Floor
from varsdaa.models import Office
from varsdaa.models import Room
from varsdaa.models import User
from varsdaa.register import handle_report


def index(request):
    return Page(
        parts__headin=html.h1("Varsdå?"),
        parts__choices=html.ul(
            html.li(
                html.a(
                    "Login",
                    attrs__href=lambda request, **_: get_adapter()
                    .get_provider(request, "google")
                    .get_login_url(request, next="/person/me/"),
                ),
            ),
            html.li(html.a("Admin", attrs__href=reverse("iommi.Admin.all_models"))),
        ),
    )


class RoomTable(Table):
    class Meta:
        auto__model = Room
        auto__include = ["display_name", "floor__office", "floor"]

        columns__display_name = dict(
            filter__include=True,
            filter__freetext=True,
            cell__url=lambda row, **_: row.get_absolute_url(),
        )
        columns__floor_office__filter__include = True
        columns__floor__filter = dict(
            include=True,
            field__choice_display_name_formatter=lambda choice,
            **_: f"{choice.office.display_name}: {choice.display_name}",
        )

        container__children__map = Map(
            rooms_all=lambda table, **_: table.rows,
            rooms_marked=lambda table, **_: table.get_visible_rows(),
        )


def where(request):
    return Page(
        parts__rooms=RoomTable(),
    )


def desks_for_users(users):
    result = []
    for user in users:
        for d in user.display_set.all():
            result.append(d.desk)
    return result


def desk_pk_for_user(user):
    for d in user.display_set.all():
        return d.desk.pk
    return None


class UserTable(Table):
    class Meta:
        model = User
        title = "Users"
        row__attrs = {
            "data-desk": lambda row, **_: desk_pk_for_user(row),
        }
        container__children__map = Map(
            desks_all=lambda table, **_: desks_for_users(table.get_visible_rows()),
            desks_marked=lambda table, **_: desks_for_users(table.rows),
            after=LAST,
        )

    avatar = Column(
        cell__value=lambda row, **_: s.get_avatar_url() if (s := row.socialaccount_set.first()) is not None else None,
        cell__format=lambda value, **_: format_html('<img src="{}" />', value) if value else "",
    )
    email = Column.from_model(
        model_field=User.email.field,
        filter__include=True,
        filter__freetext=True,
        cell__url=lambda row, **_: row.get_absolute_url(),
    )
    name = Column.from_model(
        model_field=User.name.field,
        filter__include=True,
        filter__freetext=True,
    )
    office = Column.from_model(model_field=User.office.field, filter__include=True)


def who(request):
    return Page(
        parts__users=UserTable(rows=lambda **_: User.objects.filter(is_superuser=False)),
    )


def me(request):
    return HttpResponseRedirect(request.user.get_absolute_url())


def who_details(request, email):
    user = get_object_or_404(User, email=email)

    def on_save(instance, **_):
        instance.display_set.set([])

    return Page(
        parts__heading=html.h1(user.name or user.email),
        parts__avatar=html.div(
            lambda **_: format_html(
                '<img src="{}" />',
                s.get_avatar_url(),
            )
            if (s := user.socialaccount_set.first()) is not None
            else None,
        ),
        parts__user=Form(
            editable=False,
            auto__instance=user,
            auto__include=["email", "office", "display_set"],
            fields__map=Map(
                after=LAST,
                desks_all=lambda **_: desks_for_users([user]),
                desks_marked=lambda **_: desks_for_users([user]),
            )
        ),
        parts__location=Form.edit(
            instance=user,
            include=lambda request, **_: request.user == user,
            fields__office=Field.choice_queryset(
                choices=Office.objects.all(),
            ),
            extra__on_save=on_save,
            extra__redirect_to='.',
        ),
    )


@csrf_exempt
def report_display(request):
    display_report = json.loads(request.body)
    return handle_report(display_report)


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
        display.user=user
        display.desk=desk
        display.user_updated_at=timezone.now()
        user.office = office
        user.save()

    register_display_form = Form.create(
        actions__submit__include=bool(office) & bool(floor) & bool(desk),
        title="Register display",
        model=Display,
        fields__product_name=Field(),
        fields__serial_number=Field(required=False),
        fields__alphanumeric_serial_number=Field(required=False),
        extra__pre_save=pre_save,
        extra__redirect=lambda form, **_: HttpResponseRedirect(user.get_absolute_url()),
    )
    parts.register_display = register_display_form

    return Page(parts=parts)


class FloorForm(Form):
    class Meta:
        auto__model = Floor

        @staticmethod
        def instance(floor_pk, **_):
            return get_object_or_404(Floor, pk=floor_pk)

        @staticmethod
        def fields__image__write_to_instance(field, instance, value, **kwargs):
            if value:
                instance.image = value.read()

    image = Field.image()


class ShowFloor(Page):
    form = FloorForm(editable=False)


class EditFloor(Page):
    form = FloorForm.edit()


class RoomForm(Form):
    class Meta:
        @staticmethod
        def instance(room_pk, **_):
            return get_object_or_404(Room, pk=room_pk)

        fields__map = Map(
            rooms_all=lambda instance, **_: [instance],
            rooms_marked=lambda instance, **_: [instance],
        )


class EditRoom(Page):
    form = RoomForm.edit(
        auto__model=Room,
    )


class ShowRoomForm(RoomForm):
    class Meta:
        editable = False
        auto__model = Room
        auto__include = [
            "display_name",
            "floor",
        ]

    display_name = Field()
    floor = Field()


class ShowRoom(Page):
    form = ShowRoomForm()
    edit_link = html.a("Edit", attrs__href="edit/")


class DeskForm(Form):
    class Meta:
        editable = False
        auto__model = Desk
        auto__include = [
            "floor__office",
            "floor",
        ]

        @staticmethod
        def instance(desk_pk, **_):
            return get_object_or_404(Desk, pk=desk_pk)

        fields__map = Map(
            desks_all=lambda instance, **_: Desk.objects.filter(floor=instance.floor),
            desks_marked=lambda instance, **_: [instance],
        )

    who = Field(
        display_name=_("who").title(),
        initial=lambda instance, **_: ", ".join(instance.display_set.values_list("user__name", flat=True)),
    )


class DeskShow(Page):
    form = DeskForm()


class ListFloor(Page):
    table = Table(
        auto__model=Floor,
        columns__edit=Column.edit(after=0),
        columns__image=Column.image(
            after=LAST,
        ),
    )


def floor_image(request, floor_pk):
    floor = get_object_or_404(Floor, pk=floor_pk)
    return HttpResponse(floor.image, content_type="image/png")
