from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='InstagramPost',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(choices=[('pet_portrait', 'Pet Portrait'), ('material_showcase', 'Material Showcase'), ('process_video', 'Process Video'), ('customer_testimonial', 'Customer Testimonial'), ('pricing_transparency', 'Pricing Transparency')], default='pet_portrait', max_length=32)),
                ('caption', models.TextField(help_text='Instagram caption (max 2200 chars)', max_length=2200)),
                ('image_url', models.URLField(help_text='Publicly accessible image URL (HTTPS)')),
                ('alt_text', models.CharField(blank=True, help_text='Accessibility description', max_length=256)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('scheduled', 'Scheduled'), ('publishing', 'Publishing'), ('published', 'Published'), ('failed', 'Failed')], default='draft', max_length=16)),
                ('scheduled_for', models.DateTimeField(blank=True, help_text='When to publish (null = publish immediately)', null=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('instagram_media_id', models.CharField(blank=True, help_text='Instagram media ID after publishing', max_length=128)),
                ('instagram_permalink', models.URLField(blank=True, help_text='Public Instagram URL')),
                ('impressions', models.PositiveIntegerField(default=0)),
                ('reach', models.PositiveIntegerField(default=0)),
                ('engagement', models.PositiveIntegerField(default=0)),
                ('likes', models.PositiveIntegerField(default=0)),
                ('comments', models.PositiveIntegerField(default=0)),
                ('shares', models.PositiveIntegerField(default=0)),
                ('saves', models.PositiveIntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-scheduled_for', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ContentQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
                ('description', models.TextField(blank=True)),
                ('content_type', models.CharField(choices=[('pet_portrait', 'Pet Portrait'), ('material_showcase', 'Material Showcase'), ('process_video', 'Process Video'), ('customer_testimonial', 'Customer Testimonial'), ('pricing_transparency', 'Pricing Transparency')], max_length=32)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('urgent', 'Urgent')], default='medium', max_length=16)),
                ('image_url', models.URLField(blank=True)),
                ('notes', models.TextField(blank=True, help_text='Internal notes, caption ideas, etc.')),
                ('assigned_to', models.CharField(blank=True, help_text="Who's working on this", max_length=128)),
                ('completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('instagram_post', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='queue_items', to='marketing.instagrampost')),
            ],
            options={
                'ordering': ['-priority', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='instagrampost',
            index=models.Index(fields=['status', 'scheduled_for'], name='marketing_i_status_idx'),
        ),
        migrations.AddIndex(
            model_name='instagrampost',
            index=models.Index(fields=['content_type'], name='marketing_i_content_idx'),
        ),
    ]
