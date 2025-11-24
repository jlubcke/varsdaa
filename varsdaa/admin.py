from iommi.admin import Admin

from varsdaa.iommi import Column
from varsdaa.map import Map


def fail(x):
    raise AssertionError(str(x))


class VarsdaaAdmin(Admin):
    class Meta:
        apps__auth_user__include = False
        apps__auth_group__include = False

        apps__varsdaa_user__include = True
        parts__list_varsdaa_user__columns__password__include = False

        apps__varsdaa_office__include = True
        apps__varsdaa_floor__include = True
        parts__list_varsdaa_floor__columns__image = Column.image()

        apps__varsdaa_room__include = True
        parts__edit_varsdaa_room__fields__map = Map(
            floors_marked=lambda instance, **_: [instance.floor] if instance.floor else [],
            rooms_all=lambda instance, **_: [instance],
            rooms_marked=lambda instance, **_: [instance],
        )

        apps__varsdaa_desk__include = True
        parts__edit_varsdaa_desk__fields__map = Map(
            floors_marked=lambda instance, **_: [instance.floor] if instance.floor else [],
            desks_all=lambda instance, **_: [instance],
            desks_marked=lambda instance, **_: [instance],
        )

        apps__varsdaa_registration__include = True

        apps__socialaccount_socialapp__include = True
        apps__socialaccount_socialaccount__include = True
