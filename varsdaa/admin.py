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
        apps__varsdaa_desk__include = True
        apps__varsdaa_registration__include = True

        parts__edit_varsdaa_room__fields__map = Map(
            rooms_all=lambda instance, **_: [instance],
            rooms_marked=lambda instance, **_: [instance],
        )
        parts__edit_varsdaa_desk__fields__map = Map(
            desks_all=lambda instance, **_: [instance],
            desks_marked=lambda instance, **_: [instance],
        )

        apps__socialaccount_socialapp__include = True