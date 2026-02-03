from django.apps import AppConfig


class VarsdaaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'varsdaa'

    def ready(self):
        from iommi import register_style
        from iommi import register_search_fields
        from varsdaa.style import varsdaa_style
        from varsdaa.models import User

        register_style('varsdaa_style', varsdaa_style)

        register_search_fields(model=User, search_fields=['name'], allow_non_unique=True)
