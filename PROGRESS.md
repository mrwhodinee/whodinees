# Whodinees Build — Progress

## Milestones
- [ ] M1. Repo scaffold + Django runs locally
- [ ] M2. Models + admin + DRF endpoints
- [ ] M3. Stripe + Shapeways + SendGrid services wired
- [ ] M4. React frontend + Stripe Elements
- [ ] M5. Heroku deploy green
- [ ] M6. Meshy generation — 10 products
- [ ] M7. Health check passes

## Environment notes
- Heroku app `whodinees` exists. Generation: cedar / heroku-24. Default web URL: `whodinees-8802a535baa6.herokuapp.com`
- Custom domains `whodinees.com` and `www.whodinees.com` already on app with ACM certs issued. DNS likely already pointed.
- No buildpacks yet, no addons yet, no config vars yet. No dyno formation yet.
- No Heroku CLI available; using Platform API directly via curl.
- No system pip; using `uv` (installed to /root/.local/bin) with a local `.venv` for backend Python deps.
