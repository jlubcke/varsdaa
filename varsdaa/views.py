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
from iommi import LAST
from iommi import Asset
from iommi import html
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
    instance = get_object_or_404(User, email=email)

    return Page(
        parts__heading=html.h1(instance.name or instance.email),
        parts__avatar=html.div(
            lambda **_: format_html(
                '<img src="{}" />',
                s.get_avatar_url(),
            )
            if (s := instance.socialaccount_set.first()) is not None
            else None,
        ),
        parts__user=Form(
            editable=False,
            auto__instance=instance,
            auto__include=["email", "office", "display_set"],
        ),
        parts__location=Form.edit(
            instance=instance,
            include=lambda request, **_: instance == request.user,
            fields__office=Field.choice_queryset(
                choices=Office.objects.all(),
            ),
        ),
    )


@csrf_exempt
def report_display(request):
    display_report = json.loads(request.body)
    return handle_report(display_report)



def register_display(request, email):
    parts = Struct()
    choose_office_form = AutosubmitForm(
        fields__office=Field.choice_queryset(attr=None, choices=Office.objects.all(), after=0),
    )

    parts.choose_office = choose_office_form
    office = choose_office_form.bind(request=request).fields.office.value

    choose_floor_form = AutosubmitForm(
        fields__floor=Field.choice_queryset(
            attr=None,
            choices=office.floor_set.all() if office else Floor.objects.none(),
            after=0,
        ),
    )
    parts.choose_floor = choose_floor_form
    floor = choose_floor_form.bind(request=request).fields.floor.value

    user = get_object_or_404(User, email=email)

    def new_instance(form, **_):
        desk = form.fields.desk.value
        if desk:
            Display.objects.filter(desk=desk).delete()
        return form.model()

    if office and floor:
        register_display_form = Form.create(
            title="Register display",
            auto__model=Display,
            fields__office=Field.choice_queryset(attr=None, choices=Office.objects.all(), after=0),
            fields__floor=Field.choice_queryset(attr=None, choices=Floor.objects.all(), after=1),
            fields__product_name=Field.hidden(),
            fields__serial_number=Field.hidden(required=False),
            fields__alphanumeric_serial_number=Field.hidden(required=False),
            fields__user=Field.hidden(initial=user.pk),
            fields__user_updated_at=Field.non_rendered(initial=timezone.now()),
            # fields__extra_display__help_text="This an extra display that is not the main display of the desk",
            # fields__extra_display__after="desk",
            # post_validation=post_validation,
            extra__new_instance=new_instance,
            # extra__on_save=save_person,
            extra__redirect=lambda form, **_: HttpResponseRedirect(
                f"/?user_name={form.fields.user_name.value}",
            ),
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
