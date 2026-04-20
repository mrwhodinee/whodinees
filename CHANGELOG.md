# Whodinees Build — Changelog

## 2026-04-20

### Environment
- No system pip/venv. Installed `uv` (astral) to /root/.local/bin; created `.venv` inside whodinees/.
- No Heroku CLI — using Heroku Platform API over curl with the provided bearer token.
- Heroku app `whodinees` is on the new "cedar" generation (heroku-24 stack). Custom domains already attached with ACM issued.
- Actual Heroku default hostname: `whodinees-8802a535baa6.herokuapp.com` — must be in ALLOWED_HOSTS.


### First deploy attempts
- v4 build failed: `vite: not found` — devDependencies skipped under `NODE_ENV=production` during heroku-postbuild. Fixed by using `npm ci --include=dev` in the postbuild step.
- v5 deployed but assets 404'd: collectstatic had been moved to the release phase, but Heroku release-phase filesystem changes do NOT persist into the web slug. Moved collectstatic into `bin/post_compile` (Python buildpack hook that runs during the build) so the rendered `staticfiles/` is baked into the slug.
