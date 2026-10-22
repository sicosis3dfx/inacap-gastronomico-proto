from django.apps import AppConfig


class GastronomiaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gastronomia'
    verbose_name = 'Sistema Gastronómico INACAP'

    def ready(self):
        # Estandarizamos en español la etiqueta por defecto de los selects en Django
        from django.db.models import fields
        fields.BLANK_CHOICE_LABEL = "- Selecciona una opción -"

