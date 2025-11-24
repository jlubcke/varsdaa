from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template import Template
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from iommi import LAST
from iommi import html

from varsdaa.iommi import Column
from varsdaa.iommi import Field
from varsdaa.iommi import Form
from varsdaa.iommi import Page
from varsdaa.iommi import Table
from varsdaa.map import Map
from varsdaa.models import Desk
from varsdaa.models import Floor
from varsdaa.models import Room
from varsdaa.models import User


def index(request):
    return Page(
        parts__hello=Template(
            # language=html
            """
                {% load socialaccount %}
                <il>
                    <li>
                        <a href="{% provider_login_url "google" next="/who" %}">Login with google</a>
                    </li>
                    <li>
                        <a href="/admin/">Admin login</a>
                    </li>
                </il>
            """,
        ),
    )


def desks_for_persons(persons):
    result = []
    for p in persons:
        for r in p.registration_set.all():
            result.append(r.desk)
    return result


def desk_pk_for_person(person):
    for r in person.registration_set.all():
        return r.desk.pk
    return None


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


class UserTable(Table):
    class Meta:
        model = User
        title = "Users"
        row__attrs = {
            "data-desk": lambda row, **_: desk_pk_for_person(row),
        }
        container__children__map = Map(
            desks_all=lambda table, **_: desks_for_persons(table.get_visible_rows()),
            desks_marked=lambda table, **_: desks_for_persons(table.rows),
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


def who(request):
    return Page(
        parts__users=UserTable(rows=lambda **_: User.objects.filter(is_superuser=False)),
    )


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
            auto__instance=instance,
            auto__include=["email"],
        ),
    )

def register(request, email, identifier):
    pass


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
    edit_link=html.a("Edit", attrs__href='edit/')


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
        initial=lambda instance, **_: ", ".join(instance.registration_set.values_list("user__name", flat=True)),
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
