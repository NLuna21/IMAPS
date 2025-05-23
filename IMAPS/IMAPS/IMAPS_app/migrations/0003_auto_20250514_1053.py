# Generated by Django 2.2.28 on 2025-05-14 02:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('IMAPS_app', '0002_alter_supplier_change_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplier',
            name='SupplierCode',
            field=models.CharField(help_text='Unique identifier for the supplier (manually given).', max_length=50, primary_key=True, serialize=False, unique=True),
        ),
    ]
