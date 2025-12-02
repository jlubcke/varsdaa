from django.apps import AppConfig


class VarsdaaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'varsdaa'

    def ready(self):
        from iommi import register_style

        from varsdaa.style import varsdaa_style

        register_style('varsdaa_style', varsdaa_style)
