from django.apps import AppConfig


class ImapsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'IMAPS_app'


# IMAPS_app/apps.py
from django.apps import AppConfig

class IMAPSAppConfig(AppConfig):
    name = "IMAPS_app"

    def ready(self):
        from auditlog.registry import auditlog
        from .models import (
            Supplier,
            IngredientsRawMaterials,
            PackagingRawMaterials,
            UsedIngredient,
            UsedPackaging
        )

        auditlog.register(Supplier)
        auditlog.register(IngredientsRawMaterials)
        auditlog.register(PackagingRawMaterials)
        auditlog.register(UsedIngredient)
        auditlog.register(UsedPackaging)
