# Instagram Automation Setup Guide

## Overview

Automated Instagram posting system for Whodinees marketing. Posts photos with captions on a schedule, tracks analytics, and manages content queue.

## Architecture

- **Models:** `InstagramPost` (published/scheduled posts), `ContentQueue` (draft ideas)
- **API:** Instagram Graph API via Facebook Business integration
- **Scheduling:** Django management command run via cron
- **Admin:** Full Django admin interface for managing posts

## Prerequisites

1. **Instagram Business Account** (not personal account)
2. **Facebook Page** connected to Instagram Business Account
3. **Facebook Developer App** with Instagram Graph API product

## Setup Steps

### 1. Convert Instagram to Business Account

1. Open Instagram mobile app → Settings → Account
2. Tap "Switch to Professional Account"
3. Choose "Business"
4. Connect to your Facebook Page (create one if needed)

### 2. Create Facebook Developer App

1. Go to [developers.facebook.com](https://developers.facebook.com/)
2. Click "My Apps" → "Create App"
3. Choose "Business" app type
4. Fill in:
   - App Name: "Whodinees Marketing"
   - Contact Email: hello@whodinees.com
5. Click "Create App"

### 3. Add Instagram Graph API Product

1. In your app dashboard, click "Add Product"
2. Find "Instagram Graph API" and click "Set Up"
3. No additional configuration needed here

### 4. Get Access Token

#### Method A: Graph API Explorer (Quick Test)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app from dropdown
3. Click "Get Token" → "Get User Access Token"
4. Select permissions:
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_comments`
   - `instagram_manage_insights`
   - `pages_read_engagement`
5. Click "Generate Access Token"
6. **Important:** This token expires in 1 hour. Exchange for long-lived token (see below)

#### Method B: OAuth Flow (Production)

The system includes an OAuth flow at `/admin/marketing/instagram-auth/` (future implementation).

### 5. Exchange for Long-Lived Token

Short-lived tokens expire in 1 hour. Exchange for 60-day token:

```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=SHORT_LIVED_TOKEN"
```

Response:
```json
{
  "access_token": "LONG_LIVED_TOKEN",
  "token_type": "bearer",
  "expires_in": 5183944  // ~60 days
}
```

### 6. Get Instagram Account ID

```bash
curl -X GET "https://graph.facebook.com/v18.0/me/accounts?\
fields=instagram_business_account&\
access_token=YOUR_LONG_LIVED_TOKEN"
```

Find your Instagram Business Account ID in the response:
```json
{
  "data": [{
    "instagram_business_account": {
      "id": "17841XXXXXXXXXX"  // This is your INSTAGRAM_ACCOUNT_ID
    }
  }]
}
```

### 7. Set Environment Variables on Heroku

```bash
heroku config:set INSTAGRAM_ACCESS_TOKEN="YOUR_LONG_LIVED_TOKEN" -a whodinees
heroku config:set INSTAGRAM_ACCOUNT_ID="17841XXXXXXXXXX" -a whodinees
heroku config:set FACEBOOK_APP_ID="YOUR_APP_ID" -a whodinees  
heroku config:set FACEBOOK_APP_SECRET="YOUR_APP_SECRET" -a whodinees
```

### 8. Update Django Settings

Add to `backend/whodinees/settings.py`:

```python
# Instagram API
INSTAGRAM_ACCESS_TOKEN = env('INSTAGRAM_ACCESS_TOKEN', default='')
INSTAGRAM_ACCOUNT_ID = env('INSTAGRAM_ACCOUNT_ID', default='')
FACEBOOK_APP_ID = env('FACEBOOK_APP_ID', default='')
FACEBOOK_APP_SECRET = env('FACEBOOK_APP_SECRET', default='')

INSTALLED_APPS = [
    # ... existing apps
    'marketing',
]
```

### 9. Run Migrations

```bash
python manage.py makemigrations marketing
python manage.py migrate
```

### 10. Test Connection

```bash
python manage.py test_instagram
```

Expected output:
```
Testing Instagram API connection...
✓ Connection successful

Account Info:
  Username: @whodinees
  Name: Whodinees
  Followers: 0
  Following: 0
  Media count: 0

✓ Instagram API is configured and working
```

## Usage

### Create a Post via Django Admin

1. Go to `/admin/marketing/instagrampost/add/`
2. Fill in:
   - **Content Type:** Pet Portrait, Material Showcase, etc.
   - **Caption:** Your post text (max 2200 chars)
   - **Image URL:** Publicly accessible HTTPS URL
   - **Status:** Draft → Scheduled
   - **Scheduled For:** When to publish (or leave blank for immediate)
3. Save

### Publish Scheduled Posts (Cron)

Set up Heroku Scheduler or add to `Procfile`:

```
clock: python manage.py publish_scheduled_posts --loop
```

Or run manually:
```bash
python manage.py publish_scheduled_posts
```

Dry run (test without publishing):
```bash
python manage.py publish_scheduled_posts --dry-run
```

### Manually Publish Immediately

```python
from marketing.models import InstagramPost
from marketing import instagram

post = InstagramPost.objects.create(
    content_type='pet_portrait',
    caption='Your pet. Immortalized in precious metal. 🐾✨',
    image_url='https://whodinees.com/static/showcase/golden-retriever.jpg',
    status='draft'
)

# Publish now
media_id = instagram.publish_photo(
    image_url=post.image_url,
    caption=post.caption
)

post.status = 'published'
post.instagram_media_id = media_id
post.save()
```

## Image Requirements

Instagram requires:
- **Format:** JPG or PNG
- **URL:** Publicly accessible via HTTPS
- **Size:** Min 320px, max 8MB
- **Aspect ratio:** 4:5 (portrait), 1.91:1 (landscape), 1:1 (square)

Store images at `/media/instagram/` or use CDN.

## Token Refresh

Long-lived tokens expire after 60 days. Set up auto-refresh or manual renewal:

```bash
# Renew token before expiration
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=CURRENT_LONG_LIVED_TOKEN"
```

## Rate Limits

- **200 calls per hour per app**
- **25 media creations per 24 hours**
- If exceeded, wait 1 hour before retry

## Troubleshooting

### "Invalid OAuth access token"
→ Token expired. Exchange for new long-lived token.

### "HTTPS URL is required"
→ Image URL must be HTTPS, not HTTP.

### "Media not ready"
→ Instagram is still processing. Wait 30 seconds and retry.

### "User is not authorized"
→ Instagram account is not a Business account or not linked to Facebook Page.

## Analytics

Track post performance in Django admin or via API:

```python
from marketing import instagram

insights = instagram.get_media_insights('MEDIA_ID')
print(f"Impressions: {insights['impressions']}")
print(f"Engagement: {insights['engagement']}")
```

## Content Generation

Use built-in caption generator:

```python
from marketing.instagram import generate_pet_portrait_caption

caption = generate_pet_portrait_caption(
    pet_name="Max",
    material="sterling silver",
    spot_price=2.53
)
```

## Support

- **Instagram API Docs:** https://developers.facebook.com/docs/instagram-api
- **Graph API Explorer:** https://developers.facebook.com/tools/explorer/
- **Rate Limit Status:** Check admin dashboard

---

**Ready to start posting? Run `python manage.py test_instagram` to verify setup.**
