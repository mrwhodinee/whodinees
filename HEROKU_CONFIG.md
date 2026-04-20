# Heroku Config Variables Needed

The spot pricing system requires the metals.dev API key to be set on Heroku.

## Set via Heroku CLI

```bash
heroku config:set METALS_DEV_API_KEY=RZE2CPP9DP2UITKPX9DE523KPX9DE --app whodinees
```

## Or via Heroku Dashboard

1. Go to https://dashboard.heroku.com/apps/whodinees/settings
2. Click "Reveal Config Vars"
3. Add:
   - KEY: `METALS_DEV_API_KEY`
   - VALUE: `RZE2CPP9DP2UITKPX9DE523KPX9DE`
4. Click "Add"

## Verify It's Working

After setting the key, restart the dyno and check the pricing page:
- https://whodinees.com/api/pricing/portrait

Should show live spot prices instead of fallback values.

## Current Behavior Without Key

Without the API key set, the system falls back to conservative estimates:
- Silver: $0.85/g
- Gold: $70.00/g  
- Platinum: $30.00/g

These are reasonable approximations but won't track daily market fluctuations.
