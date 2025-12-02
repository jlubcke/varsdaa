from collections.abc import Iterable

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.html import format_html
from iommi import Asset, Fragment, html
from iommi.declarative.namespace import Namespace
from iommi.endpoint import DISPATCH_PREFIX
from iommi.evaluate import evaluate_strict
from iommi.refinable import Refinable
from iommi.shortcut import with_defaults
from iommi.table import params_of_request

from varsdaa.models import Desk, Floor, Room


@with_defaults(floors_all=lambda **_: Floor.objects.all().order_by("-display_name"))
class Map(Fragment):
    class Meta:
        assets__map_js = Asset.js(children__content__template="js/map.js")

        svg__attrs = {
            "xmlns": "http://www.w3.org/2000/svg",
            "width": 1000,
            "height": 400,
            "class": {"map-svg": True},
        }

        @staticmethod
        def endpoints__image__func(value, fragment, **_):
            floor = get_object_or_404(Floor, pk=value)
            return HttpResponse(floor.image, content_type="image/png")

    svg: Namespace = Refinable()
    desks_all: Iterable[Desk] | None = Refinable()
    desks_marked: Iterable[Desk] | None = Refinable()
    rooms_all: Iterable[Room] | None = Refinable()
    rooms_marked: Iterable[Room] | None = Refinable()
    floors_all: Iterable[Room] | None = Refinable()
    floors_marked: Iterable[Room] | None = Refinable()

    def render_text_or_children(self, context=None):
        floors_all = evaluate_strict(self.floors_all, **self.iommi_evaluate_parameters()) or []
        floors_marked = evaluate_strict(self.floors_marked, **self.iommi_evaluate_parameters()) or []

        fragments = []
        request = self.get_request()
        for floor in floors_all:
            shapes = self._render_desk_shapes(floor) + self._render_room_shapes(floor)
            if not shapes and floor not in floors_marked:
                continue

            params = params_of_request(request)
            params[DISPATCH_PREFIX + self.endpoints.image.iommi_path] = floor.pk
            shapes.insert(
                0,
                html.image(
                    attrs__width=1000,
                    attrs__href="?" + params.urlencode(),
                ),
            )

            fragments.append(
                html.svg(*shapes, **self.svg).bind(request=request),
            )

        return format_html("{}\n" * len(fragments), *fragments)

    def _render_room_shapes(self, floor):
        rooms_all = evaluate_strict(self.rooms_all, **self.iommi_evaluate_parameters()) or []
        rooms_marked = evaluate_strict(self.rooms_marked, **self.iommi_evaluate_parameters())
        if not rooms_marked:
            return []

        rooms = Room.objects.filter(
            pk__in={room.pk for room in list(rooms_all) or Room.objects.all()},
        ).select_related(
            "floor",
        )

        shapes = []
        for room in rooms:
            if room.floor != floor:
                continue
            if room.x is None or room.y is None:
                continue
            shapes.append(
                html.a(
                    html.rect(
                        attrs={
                            "class": {
                                "room": True,
                                "marked": bool(room in rooms_marked),
                            },
                            "data-room": room.pk,
                            "x": room.x,
                            "y": room.y,
                            "width": room.width,
                            "height": room.height,
                        },
                    ),
                    attrs__href=room.get_absolute_url(),
                ),
            )
        return shapes

    def _render_desk_shapes(self, floor):
        desks_all = evaluate_strict(self.desks_all, **self.iommi_evaluate_parameters()) or []
        desks_marked = evaluate_strict(self.desks_marked, **self.iommi_evaluate_parameters())
        if not desks_marked:
            return []

        desks = Desk.objects.filter(
            pk__in={desk.pk for desk in list(desks_all) or Desk.objects.all()},
        ).select_related(
            "floor",
        )

        shapes = []
        for desk in desks:
            if desk.floor != floor:
                continue
            if desk.x is None or desk.y is None:
                continue

            shapes.append(
                html.a(
                    html.circle(
                        attrs={
                            "class": {
                                "desk": True,
                                "marked": bool(desk in desks_marked),
                                "connected": bool(any(desk.display_set.values_list('user', flat=True))),
                            },
                            "data-desk": desk.pk,
                            "r": 10,
                            "cx": desk.x,
                            "cy": desk.y,
                        },
                    ),
                    attrs__href=desk.get_absolute_url(),
                ),
            )

        return shapes
