# Migration for updated fee structure

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('portraits', '0003_add_size_mm_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='portraitorder',
            name='spot_price_date',
            field=models.DateTimeField(blank=True, help_text='When spot price was fetched', null=True),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='ai_processing_fee',
            field=models.DecimalField(decimal_places=2, default=Decimal('15.00'), help_text='Meshy AI model generation', max_digits=10),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='platform_fee',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Platform & processing (8% of subtotal)', max_digits=10),
        ),
        migrations.AlterField(
            model_name='portraitorder',
            name='shapeways_cost',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), help_text='Production & casting', max_digits=10),
        ),
    ]
