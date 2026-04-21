# Migration to add default value for size_mm

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portraits', '0002_expand_materials_and_pricing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='portraitorder',
            name='size_mm',
            field=models.PositiveIntegerField(default=40, help_text='Longest dimension in millimeters'),
        ),
    ]
