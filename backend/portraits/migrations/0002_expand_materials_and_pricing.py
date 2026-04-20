# Generated migration for expanded materials and pricing breakdown

from django.db import migrations, models
from decimal import Decimal


class Migration(migrations.Migration):

    dependencies = [
        ('portraits', '0001_initial'),
    ]

    operations = [
        # Update material choices
        migrations.AlterField(
            model_name='portraitorder',
            name='material',
            field=models.CharField(
                choices=[
                    ('plastic', 'Plastic'),
                    ('silver', 'Sterling Silver'),
                    ('gold_14k_yellow', '14K Yellow Gold'),
                    ('gold_14k_rose', '14K Rose Gold'),
                    ('gold_14k_white', '14K White Gold'),
                    ('gold_18k_yellow', '18K Yellow Gold'),
                    ('platinum', 'Platinum'),
                ],
                max_length=20,
            ),
        ),
        
        # Remove old fields
        migrations.RemoveField(
            model_name='portraitorder',
            name='metal_spot_price_snapshot',
        ),
        migrations.RemoveField(
            model_name='portraitorder',
            name='shapeways_cost_estimate',
        ),
        migrations.RemoveField(
            model_name='portraitorder',
            name='estimated_metal_weight_g',
        ),
        
        # Add new pricing fields
        migrations.AddField(
            model_name='portraitorder',
            name='volume_cm3',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=8),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='weight_grams',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=8),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='polycount',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='complexity_tier',
            field=models.CharField(default='moderate', max_length=16),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='spot_price_per_gram',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='material_cost',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='shapeways_cost',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='portraitorder',
            name='pricing_breakdown_json',
            field=models.JSONField(blank=True, default=dict, help_text='Full snapshot for customer records'),
        ),
    ]
