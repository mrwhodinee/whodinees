# Whodinees Build — Progress

## Milestones
- [x] M1. Repo scaffold + Django runs locally
- [x] M2. Models + admin + DRF endpoints
- [x] M3. Stripe + Shapeways + SendGrid services wired (Shapeways OAuth live-verified; Stripe PI creation live-verified; SendGrid no-op without key)
- [x] M4. React frontend + Stripe Elements (local smoke test via gunicorn)
- [x] M5. Heroku deploy green: https://whodinees-8802a535baa6.herokuapp.com/ and https://whodinees.com/ return 200
- [ ] M6. Meshy generation — 10 products (in progress on Heroku run dyno `run.8931`)
- [ ] M7. Health check

## Environment notes
- Heroku app `whodinees`, generation cedar / heroku-24.
- Custom domains `whodinees.com` + `www.whodinees.com` attached with ACM issued.
- Default Heroku URL: `https://whodinees-8802a535baa6.herokuapp.com/`
- Addons: heroku-postgresql:essential-0 (DATABASE_URL set).
- Buildpacks: heroku/nodejs → heroku/python.
- Config vars set (secrets only in Heroku + gitignored .env).
- `SENDGRID_API_KEY` intentionally unset — the email service gracefully no-ops.
- No Heroku CLI; control via Heroku Platform API over curl.

## Admin
- URL: https://whodinees-8802a535baa6.herokuapp.com/admin/
- Username: `admin`
- Email: `mrmaywho+whodinees@example.com`
- Password: **BXdWYherKbTCagOtFM9sGI!-vdTPZ9**  (delivered once; change after first login)
