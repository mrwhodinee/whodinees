# Whodinees Knowledge Base

Complete reference for all services, APIs, and integrations used in the Whodinees platform.

**Last Updated:** 2026-04-28  
**Current Version:** v69

---

## 🏗️ Infrastructure

### Hosting

**Heroku**
- App name: `whodinees`
- URL: `whodinees-8802a535baa6.herokuapp.com`
- Region: US
- Dyno type: Basic (web.1)
- API key: `bb6d5a91-9250-4457-8c04-9af60cf811cc`
- CLI: `heroku logs --tail --app whodinees`

**Domain**
- Primary: whodinees.com
- Registrar: [TBD - user to specify]
- DNS: Currently pointing to Heroku, Cloudflare setup pending

---

## 📊 Analytics & Monitoring

### Sentry (Error Monitoring)
- **Organization:** Mr. May Who LLC
- **Project:** whodinees
- **DSN:** `https://449044596d856269142fffc5a5b544c7@o4511297467842560.ingest.us.sentry.io/4511297532592128`
- **Integration:** Django backend + React frontend
- **Webhook:** `/api/sentry/webhook/` (sends Telegram alerts)
- **Test endpoints:**
  - `/api/test/sentry-error` (raises exception)
  - `/api/test/sentry-message` (logs info message)

**Configuration:**
```python
# backend/whodinees/settings.py
sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment="production" if not DEBUG else "development",
    traces_sample_rate=0.1,
)
```

### Google Analytics 4
- **Account:** hello@whodinees.com
- **Property:** Whodinees
- **Measurement ID:** `G-8D2K8DLQ69`
- **Integration:** react-ga4 in frontend

**Custom Events:**
- `upload_started` - Photo upload begins
- `model_generated` - Meshy AI completes 3D model
- `material_selected` - Customer chooses material
- `begin_checkout` - Proceeding to payment
- `purchase` - Order completed
- `upload_abandoned` - 24h/72h abandonment tracking

**Configuration:**
```javascript
// frontend/src/main.jsx
import ReactGA from 'react-ga4'
if (import.meta.env.PROD) {
  ReactGA.initialize('G-8D2K8DLQ69')
}
```

### Hotjar (Session Recording)
- **Site ID:** [embedded in script URL]
- **Script:** `https://t.contentsquare.net/uxa/a85643ae28f76.js`
- **Location:** `frontend/index.html`
- **Pages tracked:** Upload, model viewer, checkout, payment confirmation

---

## 🔐 Security

### Rate Limiting (django-ratelimit)
```python
# Upload endpoint
@ratelimit(key='ip', rate='5/h', method='POST')
@ratelimit(key='ip', rate='20/d', method='POST')

# Quote endpoint
@ratelimit(key='ip', rate='30/h', method='POST')

# Order endpoint
@ratelimit(key='ip', rate='10/d', method='POST')
```

**Error handler:** `backend/portraits/ratelimit_handler.py`
- Friendly error messages
- Telegram alerts on daily limit abuse (order endpoint only)

### Cloudflare (Pending Setup)
**Account:** hello@whodinees.com  
**Setup guide:** `CLOUDFLARE_SETUP.md` in repo root

**Features to enable:**
- SSL/TLS: Full (strict)
- DDoS protection: Automatic
- Bot management: Free tier
- CDN caching: Page Rules configured
- HTTP/3, Brotli, Early Hints

**Page Rules:**
1. `/static/*` → Cache 30 days
2. `/api/*` → Bypass cache
3. `/media/*` → Cache 7 days

---

## 💳 Payment Processing

### Stripe
- **Account:** hello@whodinees.com
- **Mode:** Production
- **Integration:** Django backend (stripe-python)
- **Webhook endpoint:** `/api/stripe/webhook/`
- **Webhook secret:** [Set in Heroku config]

**Payment Flow:**
1. $25 deposit (portrait generation)
2. Full payment after customer approval
3. Webhooks trigger order processing

**Environment Variables:**
```bash
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

---

## 🤖 AI Services

### Meshy AI (3D Model Generation)
- **API:** https://api.meshy.ai/v2
- **Integration:** `backend/portraits/services/meshy_portrait.py`
- **Flow:** Photo → 3 variants → Customer selects → GLB file
- **API Key:** [Set in Heroku config]

**Endpoints Used:**
- `POST /v2/image-to-3d` - Submit photo
- `GET /v2/image-to-3d/{task_id}` - Poll status
- GLB download via signed URL (proxied through `/api/portraits/{id}/model.glb`)

**CORS Proxy:**
```python
# backend/portraits/views.py
@api_view(["GET"])
def proxy_glb(request, portrait_id):
    # Fetches GLB from Meshy, serves with CORS headers
```

---

## 🏭 Manufacturing

### Shapeways (3D Printing)
- **API:** https://api.shapeways.com/
- **Integration:** Placeholder in `backend/portraits/services/`
- **Status:** Not fully integrated yet
- **Materials:** Plastic, Sterling Silver, 14K Gold, Platinum

**Planned Flow:**
1. Upload approved GLB to Shapeways
2. Create order via API
3. Track production status
4. Retrieve tracking number

---

## 📧 Email Services

### SendGrid
- **Account:** hello@whodinees.com
- **From address:** hello@whodinees.com
- **API Key:** [Set in Heroku config]
- **Integration:** `backend/portraits/services/email.py`

**Email Types:**
1. Order confirmation (with invoice PDF attachment)
2. Abandoned upload recovery (24h + 72h)
3. Review request (7-10 days post-delivery)

**Configuration:**
```python
# backend/whodinees/settings.py
SENDGRID_API_KEY = env("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = "hello@whodinees.com"
```

---

## 📱 Notifications

### Telegram Bot
- **Bot token:** `8267795694:AAGBGJb3akfajnI35Qp65G9ZLLfeJpzF50s`
- **Chat ID:** `1972458437` (Mr May Who)
- **Integration:** Sentry webhook, rate limit alerts

**Alerts Sent:**
- Sentry errors (production only)
- Rate limit abuse (order endpoint)
- [Future: Order notifications, delivery updates]

---

## 🔍 SEO

### Google Search Console
- **Property:** whodinees.com
- **Owner:** hello@whodinees.com
- **Sitemap:** https://whodinees.com/sitemap.xml
- **Status:** Property added, awaiting verification

**Meta Tags:**
```html
<title>Whodinees — Turn Your Pet Photo Into Precious Metal</title>
<meta name="description" content="Custom 3D printed jewelry priced at live spot rates..." />
```

**Structured Data:**
- Schema.org Organization
- Product offerings (Sterling Silver, Gold, Platinum)
- Price range: $50-$5000

---

## 📄 Document Generation

### wkhtmltopdf (Invoice PDFs)
- **Version:** 0.12.6 (with patched qt)
- **Integration:** `backend/portraits/invoice_generator.py`
- **Template:** `backend/portraits/templates/portraits/invoice.html`

**Invoice Contents:**
- Company: Mr. May Who LLC
- Order details, pricing breakdown
- Spot price timestamp
- Investment note
- Stored in `invoice_pdf` FileField on PortraitOrder

---

## 🗄️ Database

### PostgreSQL (Heroku Postgres)
- **Plan:** Mini (10k rows)
- **Attached to:** whodinees app
- **Connection:** Auto-configured via `DATABASE_URL`

**Models:**
- `PetPortrait` - Customer uploads, Meshy tasks
- `PortraitOrder` - Orders with pricing, shipping
- `PortraitReview` - Customer reviews + photos

**Migrations:**
- Run automatically on Heroku deploy (release phase)
- Local: `python backend/manage.py migrate`

---

## 🛠️ Developer Tools

### GitHub
- **Repo:** mrwhodinee/whodinees
- **Owner:** mrmaywho
- **Token:** [Stored in local git config, not in repo]
- **Branches:** `main` (production)

**Workflow:**
```bash
git add -A
git commit -m "Description"
git push origin main
git push heroku main  # Deploys to production
```

### Heroku CLI Commands
```bash
# Logs
heroku logs --tail --app whodinees

# Shell
heroku run bash --app whodinees

# Config
heroku config --app whodinees
heroku config:set KEY=value --app whodinees

# Migrations
heroku run python backend/manage.py migrate --app whodinees

# One-off tasks
heroku run python backend/manage.py send_abandoned_recovery --app whodinees
```

### Testing Tools
- **Playwright:** Browser automation (`playwright install chromium`)
- **curl:** API testing
- **Postman/newman:** API collection testing

---

## 📅 Scheduled Tasks (Pending Activation)

### Heroku Scheduler
**Add-on:** Not activated yet  
**When activated, add these jobs:**

1. **Abandoned Upload Recovery**
   - Command: `python backend/manage.py send_abandoned_recovery`
   - Frequency: Daily at 10:00 AM UTC
   - Purpose: Send 24h and 72h recovery emails

2. **Review Requests**
   - Command: `python backend/manage.py send_review_requests`
   - Frequency: Daily at 10:00 AM UTC
   - Purpose: Send review requests 7-10 days post-delivery

---

## 🚀 Deployment Checklist

Before each deploy:
1. ✅ Test locally if possible
2. ✅ Commit with descriptive message
3. ✅ Push to GitHub: `git push origin main`
4. ✅ Deploy to Heroku: `git push heroku main`
5. ✅ Watch logs: `heroku logs --tail`
6. ✅ Test in production
7. ✅ Verify Sentry receives events (if error-related change)

---

## 📞 Support Contacts

**Primary Contact:** Mr. May Who  
**Email:** hello@whodinees.com  
**Telegram:** @mrmaywho (Chat ID: 1972458437)

**Service Support:**
- Heroku: https://help.heroku.com
- Sentry: https://sentry.io/support
- Stripe: https://support.stripe.com
- Cloudflare: https://support.cloudflare.com
- SendGrid: https://support.sendgrid.com

---

*This knowledge base is the single source of truth for all Whodinees integrations and services.*
