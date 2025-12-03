from allauth.socialaccount.adapter import get_adapter
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from iommi import LAST, html

from varsdaa.iommi import Column, Field, Form, Page, Table
from varsdaa.map import Map
from varsdaa.models import Desk, Floor, Office, Room, User


def index(request):
    return Page(
        parts__heading=html.h1("Varsdå?"),
        parts__items=html.ul(
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
        # Clear all previously connected displays
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
            ),
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
