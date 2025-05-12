from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('IMAPS_app', '0003_supplier_change_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supplier',
            name='change_status',
        ),
        migrations.RemoveField(
            model_name='ingredientsrawmaterials',
            name='change_status',
        ),
        migrations.RemoveField(
            model_name='packagingrawmaterials',
            name='change_status',
        ),
        migrations.RemoveField(
            model_name='usedingredient',
            name='change_status',
        ),
        migrations.RemoveField(
            model_name='usedpackaging',
            name='change_status',
        ),
    ]
