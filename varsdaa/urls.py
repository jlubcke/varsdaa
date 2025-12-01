from django.urls import include
from django.urls import path

import varsdaa.views as views
from varsdaa.admin import VarsdaaAdmin
from varsdaa.views import DeskShow
from varsdaa.views import EditFloor
from varsdaa.views import EditRoom
from varsdaa.views import ListFloor
from varsdaa.views import ShowFloor
from varsdaa.views import ShowRoom

urlpatterns = [
    path("", views.index, name="index"),
    path("room/", views.where, name="where"),
    path("room/<int:room_pk>/", ShowRoom().as_view(), name="room_show"),
    path("room/<int:room_pk>/edit/", EditRoom().as_view(), name="room_edit"),

    path("person/", views.who, name="who"),
    path("person/me/", views.me, name="me"),
    path("person/<email>/", views.who_details, name="who_details"),
    path("person/<email>/register_display", views.register_display, name="register_display"),

    path("desk/<int:desk_pk>/", DeskShow().as_view(), name="desk_show"),
    path("floor/", ListFloor().as_view(), name="floor_list"),
    path("floor/<int:floor_pk>/", ShowFloor().as_view(), name="floor_edit"),
    path("floor/<int:floor_pk>/edit/", EditFloor().as_view(), name="floor_edit"),
    path("floor/<int:floor_pk>/image/", views.floor_image, name="floor_image"),

    path("admin/", include(VarsdaaAdmin.urls())),

    path("report_display/", views.report_display, name="report_display")
]
