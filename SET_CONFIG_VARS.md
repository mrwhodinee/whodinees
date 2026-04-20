# Set Required Config Variables on Heroku

Two API keys need to be set for the site to work fully:

## 1. Metals.dev (Spot Pricing)
Without this, pricing uses fallback estimates instead of live market prices.

## 2. SendGrid/Twilio (Order Emails)  
Without this, order confirmation emails won't send (gracefully skipped).

---

## Option A: Heroku Dashboard (Easiest)

1. Go to: https://dashboard.heroku.com/apps/whodinees/settings
2. Click **"Reveal Config Vars"**
3. Add both:

| KEY | VALUE |
|-----|-------|
| `METALS_DEV_API_KEY` | `RZE2CPP9DP2UITKPX9DE523KPX9DE` |
| `SENDGRID_API_KEY` | `SK7e25d07ef0658cb03377fae3d8f13ef4` |

4. Click **"Add"** for each
5. Heroku will automatically restart the app

---

## Option B: Heroku CLI

If you have the Heroku CLI installed:

```bash
heroku config:set \
  METALS_DEV_API_KEY=RZE2CPP9DP2UITKPX9DE523KPX9DE \
  SENDGRID_API_KEY=SK7e25d07ef0658cb03377fae3d8f13ef4 \
  --app whodinees
```

---

## Verify It's Working

### Spot Pricing
Visit: https://whodinees.com/api/pricing/portrait

Should show live market prices instead of fallbacks (silver ~$0.85/g, gold ~$70/g).

### Email
Place a test order. You should receive a confirmation email with full pricing breakdown.

---

## Security Note

These API keys are specific to this project. If you need to rotate them later:
- Metals.dev: Generate new key at https://metals.dev/dashboard
- SendGrid: Generate new key at https://app.sendgrid.com/settings/api_keys
