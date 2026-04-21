"""Marketing content scheduling and tracking models."""

from django.db import models
from django.utils import timezone


class InstagramPost(models.Model):
    """Scheduled or published Instagram post."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('publishing', 'Publishing'),
        ('published', 'Published'),
        ('failed', 'Failed'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('pet_portrait', 'Pet Portrait'),
        ('material_showcase', 'Material Showcase'),
        ('process_video', 'Process Video'),
        ('customer_testimonial', 'Customer Testimonial'),
        ('pricing_transparency', 'Pricing Transparency'),
    ]
    
    # Content
    content_type = models.CharField(max_length=32, choices=CONTENT_TYPE_CHOICES, default='pet_portrait')
    caption = models.TextField(max_length=2200, help_text="Instagram caption (max 2200 chars)")
    image_url = models.URLField(help_text="Publicly accessible image URL (HTTPS)")
    alt_text = models.CharField(max_length=256, blank=True, help_text="Accessibility description")
    
    # Scheduling
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft')
    scheduled_for = models.DateTimeField(null=True, blank=True, help_text="When to publish (null = publish immediately)")
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Instagram metadata
    instagram_media_id = models.CharField(max_length=128, blank=True, help_text="Instagram media ID after publishing")
    instagram_permalink = models.URLField(blank=True, help_text="Public Instagram URL")
    
    # Analytics (updated periodically)
    impressions = models.PositiveIntegerField(default=0)
    reach = models.PositiveIntegerField(default=0)
    engagement = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    comments = models.PositiveIntegerField(default=0)
    shares = models.PositiveIntegerField(default=0)
    saves = models.PositiveIntegerField(default=0)
    
    # Tracking
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-scheduled_for', '-created_at']
        indexes = [
            models.Index(fields=['status', 'scheduled_for']),
            models.Index(fields=['content_type']),
        ]
    
    def __str__(self):
        return f"{self.content_type} - {self.status} - {self.caption[:50]}"
    
    def is_ready_to_publish(self):
        """Check if post is ready to publish now."""
        if self.status != 'scheduled':
            return False
        if not self.scheduled_for:
            return True
        return self.scheduled_for <= timezone.now()


class ContentQueue(models.Model):
    """Queue of content ideas and drafts."""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    content_type = models.CharField(max_length=32, choices=InstagramPost.CONTENT_TYPE_CHOICES)
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default='medium')
    
    # References
    image_url = models.URLField(blank=True)
    notes = models.TextField(blank=True, help_text="Internal notes, caption ideas, etc.")
    
    # Workflow
    assigned_to = models.CharField(max_length=128, blank=True, help_text="Who's working on this")
    completed = models.BooleanField(default=False)
    instagram_post = models.ForeignKey(InstagramPost, null=True, blank=True, on_delete=models.SET_NULL, related_name='queue_items')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"[{self.priority}] {self.title}"
