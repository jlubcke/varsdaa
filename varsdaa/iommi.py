import iommi
from django.template import Template
from django.utils.html import format_html
from iommi import Asset
from iommi.admin import Messages
from iommi.shortcut import with_defaults

from varsdaa.models import Desk, Room


class Table(iommi.Table):
    class Meta:
        page_size = 5
        query__advanced__template = None
        row__attrs = {
            "data-desk": lambda row, **_: row.pk if isinstance(row, Desk) else None,
            "data-room": lambda row, **_: row.pk if isinstance(row, Room) else None,
        }


class Column(iommi.Column):
    @classmethod
    @with_defaults(
        cell__value=lambda row, **_: row,
        cell__format=lambda value, **_: format_html(
            '<img  style="height:100px;" src="{}image/" />',
            value.get_absolute_url(),
        ),
    )
    def image(cls, **kwargs):
        return cls(**kwargs)


class MenuItem(iommi.MenuItem):
    pass


class Menu(iommi.Menu):
    index = MenuItem(display_name='Tebax', url='/')
    where = MenuItem(display_name="Vars", url="/room/")
    who = MenuItem(display_name="Vem", url="/person/")
    admin = MenuItem(url="/admin/", include=lambda request, **_: request.user.is_superuser)
    logout = MenuItem(url="/admin/logout", include=lambda request, **_: request.user.is_authenticated)


class Page(iommi.Page):
    class Meta:
        assets__style = Asset.css(
            # language=css
            """
            .room {
                fill: rgba(0, 0, 255, 0.1);
            }

            .desk {
                fill: rgba(0, 123, 255, 0.1);
                stroke: black;
            }

            .marked {
                fill: rgba(0, 255, 0, 0.1)
            }

            .hover {
                fill: rgba(200, 200, 200, 0.2);

            }
            """,
            tag="style",
        )

    menu = Menu()
    messages = Messages()


class Form(iommi.Form):
    pass


class Field(iommi.Field):
    @classmethod
    @with_defaults(
        template=Template(
            # language=html
            """ \
                <div{{ field.attrs }}>
                    {{ field.label }}
                    {{ field.input }}
                    {% if field.value %}
                    <img class="mt-3 mb-3" style="height:100px" src="/floor/{{ field.form.instance.pk }}/image/" />
                    {% endif %}
                    {{ field.help }}
                {{ field.errors }}
                </div>
            """,
        ),
    )
    def image(cls, **kwargs):
        return super().image(**kwargs)


class EditTable(iommi.EditTable):
    pass


class EditColumn(iommi.EditColumn):
    pass
