"""Django admin for marketing content."""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import InstagramPost, ContentQueue


@admin.register(InstagramPost)
class InstagramPostAdmin(admin.ModelAdmin):
    list_display = ['preview_caption', 'content_type', 'status_badge', 'scheduled_for', 'published_at', 'engagement_summary']
    list_filter = ['status', 'content_type', 'created_at']
    search_fields = ['caption']
    readonly_fields = ['instagram_media_id', 'instagram_permalink', 'published_at', 'created_at', 'updated_at', 'analytics_summary']
    
    fieldsets = [
        ('Content', {
            'fields': ['content_type', 'caption', 'image_url', 'alt_text']
        }),
        ('Scheduling', {
            'fields': ['status', 'scheduled_for', 'published_at']
        }),
        ('Instagram Data', {
            'fields': ['instagram_media_id', 'instagram_permalink'],
            'classes': ['collapse']
        }),
        ('Analytics', {
            'fields': ['analytics_summary', 'impressions', 'reach', 'engagement', 'likes', 'comments', 'shares', 'saves'],
            'classes': ['collapse']
        }),
        ('Tracking', {
            'fields': ['error_message', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    def preview_caption(self, obj):
        return obj.caption[:60] + ('...' if len(obj.caption) > 60 else '')
    preview_caption.short_description = 'Caption'
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'scheduled': 'blue',
            'publishing': 'orange',
            'published': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def engagement_summary(self, obj):
        if obj.status != 'published':
            return '—'
        total = obj.likes + obj.comments + obj.saves + obj.shares
        return f"💜 {obj.likes} | 💬 {obj.comments} | 🔖 {obj.saves} | ↗️ {obj.shares}"
    engagement_summary.short_description = 'Engagement'
    
    def analytics_summary(self, obj):
        if obj.status != 'published':
            return 'Post not published yet'
        
        engagement_rate = (obj.engagement / obj.impressions * 100) if obj.impressions > 0 else 0
        
        return format_html(
            '<table style="width: 100%; border-collapse: collapse;">'
            '<tr><th style="text-align: left; padding: 8px; background: #f0f0f0;">Metric</th><th style="text-align: right; padding: 8px; background: #f0f0f0;">Value</th></tr>'
            '<tr><td style="padding: 8px; border-top: 1px solid #ddd;">Impressions</td><td style="text-align: right; padding: 8px; border-top: 1px solid #ddd;">{:,}</td></tr>'
            '<tr><td style="padding: 8px; border-top: 1px solid #ddd;">Reach</td><td style="text-align: right; padding: 8px; border-top: 1px solid #ddd;">{:,}</td></tr>'
            '<tr><td style="padding: 8px; border-top: 1px solid #ddd;">Engagement</td><td style="text-align: right; padding: 8px; border-top: 1px solid #ddd;">{:,}</td></tr>'
            '<tr><td style="padding: 8px; border-top: 1px solid #ddd;">Engagement Rate</td><td style="text-align: right; padding: 8px; border-top: 1px solid #ddd; font-weight: bold;">{:.2f}%</td></tr>'
            '</table>',
            obj.impressions, obj.reach, obj.engagement, engagement_rate
        )
    analytics_summary.short_description = 'Analytics Summary'
    
    actions = ['mark_as_scheduled', 'mark_as_draft']
    
    def mark_as_scheduled(self, request, queryset):
        count = queryset.update(status='scheduled')
        self.message_user(request, f'{count} post(s) marked as scheduled')
    mark_as_scheduled.short_description = 'Mark as scheduled'
    
    def mark_as_draft(self, request, queryset):
        count = queryset.update(status='draft')
        self.message_user(request, f'{count} post(s) marked as draft')
    mark_as_draft.short_description = 'Mark as draft'


@admin.register(ContentQueue)
class ContentQueueAdmin(admin.ModelAdmin):
    list_display = ['title', 'content_type', 'priority_badge', 'assigned_to', 'completed', 'created_at']
    list_filter = ['content_type', 'priority', 'completed']
    search_fields = ['title', 'description', 'notes']
    
    fieldsets = [
        (None, {
            'fields': ['title', 'description', 'content_type', 'priority']
        }),
        ('Content', {
            'fields': ['image_url', 'notes']
        }),
        ('Workflow', {
            'fields': ['assigned_to', 'completed', 'instagram_post']
        }),
    ]
    
    def priority_badge(self, obj):
        colors = {
            'low': '#90CAF9',
            'medium': '#FFB74D',
            'high': '#FF8A65',
            'urgent': '#E57373',
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.priority.upper()
        )
    priority_badge.short_description = 'Priority'
