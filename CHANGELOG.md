# Whodinees Build — Changelog

## 2026-04-20

### Environment
- No system pip/venv. Installed `uv` (astral) to /root/.local/bin; created `.venv` inside whodinees/.
- No Heroku CLI — using Heroku Platform API over curl with the provided bearer token.
- Heroku app `whodinees` is on the new "cedar" generation (heroku-24 stack). Custom domains already attached with ACM issued.
- Actual Heroku default hostname: `whodinees-8802a535baa6.herokuapp.com` — must be in ALLOWED_HOSTS.

