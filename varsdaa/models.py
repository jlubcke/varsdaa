from typing import ClassVar

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import BinaryField
from django.db.models import CharField
from django.db.models import DateTimeField
from django.db.models import EmailField
from django.db.models import ForeignKey
from django.db.models import IntegerField
from django.db.models import Model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from varsdaa.managers import UserManager


class User(AbstractUser):
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore[assignment]
    last_name = None  # type: ignore[assignment]
    email = EmailField(_("email address"), unique=True)
    username = None  # type: ignore[assignment]

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects: ClassVar[UserManager] = UserManager()

    def get_absolute_url(self) -> str:
        return reverse("who_details", kwargs={"email": self.email})

    office = ForeignKey(to='Office', on_delete=models.CASCADE, null=True)
    office_updated_at = DateTimeField(auto_now=True)


class Office(Model):
    display_name = CharField(max_length=255)

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return f"<Office pk={self.pk}, display_name={self.display_name!r}>"


class Floor(Model):
    display_name = CharField(max_length=255)
    office = ForeignKey(
        to=Office,
        null=False,
        on_delete=models.CASCADE,
    )
    image = BinaryField(editable=True, null=True)

    class Meta:
        verbose_name = _("floor")
        verbose_name_plural = _("floors")

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return f"<Floor pk={self.pk}, display_name={self.display_name!r}, office_id={self.office_id}>"

    def get_absolute_url(self):
        return f"/floor/{self.pk}/"


class Room(Model):
    display_name = CharField(max_length=255)
    floor = ForeignKey(
        to=Floor,
        null=False,
        on_delete=models.CASCADE,
    )
    x = IntegerField(null=True)
    y = IntegerField(null=True)
    width = IntegerField(null=True)
    height = IntegerField(null=True)

    class Meta:
        verbose_name = _("room")
        verbose_name_plural = _("rooms")

    def __str__(self):
        return self.display_name

    def __repr__(self):
        return (
            f"<Room pk={self.pk}, display_name={self.display_name!r}, floor_id={self.floor_id}, "
            f"x={self.x}, y={self.y}, width={self.width}, height={self.height}>"
        )

    def get_absolute_url(self):
        return f"/room/{self.pk}/"


class Desk(Model):
    floor = ForeignKey(
        to=Floor,
        null=False,
        on_delete=models.CASCADE,
    )
    x = IntegerField(null=True)
    y = IntegerField(null=True)

    class Meta:
        verbose_name = _("desk")
        verbose_name_plural = _("desks")

    def __str__(self):
        return f"Desk #{self.pk}"

    def __repr__(self):
        return f"<Desk pk={self.pk}, floor_id={self.floor_id}, x={self.x}, y={self.y}>"

    def get_absolute_url(self):
        return f"/desk/{self.pk}/"


class Display(Model):
    desk = ForeignKey(to=Desk, on_delete=models.CASCADE, null=True)
    product_name =CharField(max_length=255)
    serial_number = CharField(max_length=255)
    alphanumeric_serial_number = CharField(max_length=255)
    user = ForeignKey(to=User, on_delete=models.CASCADE, null=True)
    user_updated_at = DateTimeField(null=True)


