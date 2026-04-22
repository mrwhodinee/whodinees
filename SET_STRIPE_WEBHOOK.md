# Set Stripe Webhook Secret on Heroku

## Quick Command

Run this now:

```bash
heroku config:set STRIPE_WEBHOOK_SECRET="whsec_mFC4aZnrfwQQAbz8L40s98TsKiW1g5Ms" -a whodinees
```

## Or via Dashboard

1. Go to: https://dashboard.heroku.com/apps/whodinees/settings
2. Click "Reveal Config Vars"
3. Add new var:
   - Key: `STRIPE_WEBHOOK_SECRET`
   - Value: `whsec_mFC4aZnrfwQQAbz8L40s98TsKiW1g5Ms`
4. Save

## What this fixes

When a customer pays the $19 deposit:
1. Stripe charges the card
2. Stripe calls our webhook at `/api/portraits/stripe/portrait-webhook/`
3. Our backend verifies the call is really from Stripe (using this secret)
4. Backend marks `deposit_paid=True`
5. Meshy AI generation starts
6. User sees progress (no more loop!)

Without this secret, the webhook is ignored and the loop continues.

## Test after setting

1. Upload a photo at whodinees.com/portraits
2. Pay $19 deposit with test card: 4242 4242 4242 4242
3. You should see "Generating your 3D model..." (not loop back to payment)
