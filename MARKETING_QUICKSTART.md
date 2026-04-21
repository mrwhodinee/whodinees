# Marketing Quick Start Guide

## Instagram Setup (5 minutes)

### 1. Set Environment Variables on Heroku

You need 4 Instagram credentials. Follow `INSTAGRAM_SETUP.md` for details, or use these commands:

```bash
# After getting your credentials from Facebook Developer Portal:
heroku config:set INSTAGRAM_ACCESS_TOKEN="YOUR_TOKEN_HERE" -a whodinees
heroku config:set INSTAGRAM_ACCOUNT_ID="17841XXXXXXXXXX" -a whodinees
heroku config:set FACEBOOK_APP_ID="YOUR_APP_ID" -a whodinees
heroku config:set FACEBOOK_APP_SECRET="YOUR_APP_SECRET" -a whodinees
```

### 2. Test Connection

```bash
heroku run python backend/manage.py test_instagram -a whodinees
```

Expected output:
```
✓ Connection successful
Account Info:
  Username: @whodinees
  Followers: X
✓ Instagram API is configured and working
```

### 3. Create Sample Posts

```bash
heroku run python backend/manage.py create_sample_posts -a whodinees
```

This creates:
- 3 sample Instagram posts (1 draft, 2 scheduled)
- 3 content queue items

### 4. Publish Your First Post

**Option A: Django Admin (Recommended)**

1. Go to https://whodinees.com/admin/marketing/instagrampost/
2. Find the Golden Retriever post (status: draft)
3. Change status to "scheduled"
4. Set "Scheduled for" to NOW (or leave blank)
5. Save
6. Run: `heroku run python backend/manage.py publish_scheduled_posts -a whodinees`

**Option B: Command Line**

```bash
# Dry run (shows what would be published)
heroku run python backend/manage.py publish_scheduled_posts --dry-run -a whodinees

# Actually publish
heroku run python backend/manage.py publish_scheduled_posts -a whodinees
```

### 5. Set Up Auto-Publishing (Heroku Scheduler)

1. Go to https://dashboard.heroku.com/apps/whodinees/scheduler
2. Click "Create job"
3. Schedule: Every 10 minutes
4. Command: `python backend/manage.py publish_scheduled_posts`
5. Save

Now posts will auto-publish when their scheduled time arrives.

## Creating Real Content

### Method 1: Django Admin (Visual)

1. Go to https://whodinees.com/admin/marketing/instagrampost/add/
2. Fill in:
   - Content Type: Pet Portrait
   - Caption: Your text (use the caption generator for inspiration)
   - Image URL: https://whodinees.com/static/showcase/your-image.jpg
   - Status: Scheduled
   - Scheduled For: When to post
3. Save

### Method 2: Python Script

```python
from marketing.models import InstagramPost
from marketing.instagram import generate_pet_portrait_caption
from django.utils import timezone
from datetime import timedelta

# Create post
post = InstagramPost.objects.create(
    content_type='pet_portrait',
    caption=generate_pet_portrait_caption(
        pet_name="Buddy",
        material="platinum",
        spot_price=66.40
    ),
    image_url='https://whodinees.com/static/showcase/your-pet.jpg',
    status='scheduled',
    scheduled_for=timezone.now() + timedelta(hours=2)  # 2 hours from now
)
```

### Method 3: Content Queue Workflow

1. Go to https://whodinees.com/admin/marketing/contentqueue/
2. Create ideas/drafts with priority
3. When ready, convert to InstagramPost
4. Schedule and publish

## Image Requirements

Instagram requires:
- **Format:** JPG or PNG
- **Public URL:** Must be HTTPS and accessible
- **Size:** Min 320px, max 8MB
- **Aspect ratio:** 1:1 (square) or 4:5 (portrait) works best

Upload images to:
- `/media/instagram/` on Heroku
- Or use existing showcase images at `/static/showcase/`

## Caption Tips

**Good captions:**
- Lead with emotion or value
- Include CTA (link in bio, DM us, visit site)
- Use relevant hashtags (#petportrait #preciousmetal)
- Max 2200 characters (Instagram limit)

**Use the generator:**
```python
from marketing.instagram import generate_pet_portrait_caption

caption = generate_pet_portrait_caption(
    pet_name="Max",
    material="sterling silver",
    spot_price=2.53
)
```

Returns captions with:
- Pet name
- Material
- Live spot pricing
- Value proposition
- Clear CTA

## Posting Schedule

Recommended:
- **Frequency:** 1-2 posts per day
- **Best times:** 9 AM, 12 PM, 6 PM (your timezone)
- **Content mix:**
  - 50% pet portraits
  - 25% pricing transparency
  - 25% process/behind-scenes

## Analytics

Track performance in Django admin:
- Impressions, reach, engagement
- Likes, comments, saves, shares
- Engagement rate calculated automatically

Refresh analytics:
```bash
heroku run python backend/manage.py update_instagram_insights -a whodinees
```
(Command coming soon)

## Troubleshooting

### "Invalid OAuth access token"
Token expired (60 days). Renew:
```bash
curl -X GET "https://graph.facebook.com/v18.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=YOUR_APP_ID&\
client_secret=YOUR_APP_SECRET&\
fb_exchange_token=CURRENT_TOKEN"
```

### "Image URL not accessible"
- Must be HTTPS
- Must be publicly accessible
- Try: `curl -I YOUR_IMAGE_URL`

### "Rate limit exceeded"
Instagram limits:
- 200 API calls per hour
- 25 media creations per 24 hours

Wait 1 hour, then retry.

## First Week Strategy

**Day 1-2:** Set up + test
- Configure Instagram credentials
- Create 5 draft posts
- Publish 1 test post
- Verify it appears on Instagram

**Day 3-7:** Ramp up
- Schedule 1-2 posts per day
- Mix content types
- Monitor engagement
- Adjust timing based on performance

**Week 2+:** Scale
- Increase to 2 posts per day
- Add Stories (future feature)
- Engage with comments
- Track top-performing content

---

**Ready to start? Run:** `heroku run python backend/manage.py test_instagram -a whodinees`
