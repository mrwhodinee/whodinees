# Cloudflare Setup for Whodinees

This guide walks through setting up Cloudflare for whodinees.com.

## Benefits

- **CDN**: Cache static assets globally for faster load times
- **DDoS Protection**: Automatic protection against attacks
- **SSL/TLS**: Free SSL certificates with automatic renewal
- **Performance**: Minification, compression, HTTP/3
- **Analytics**: Traffic insights and bot detection
- **WAF**: Web Application Firewall (paid plans)

---

## Setup Steps

### 1. Create Cloudflare Account

1. Go to https://dash.cloudflare.com/sign-up
2. Sign up with: **hello@whodinees.com**
3. Verify email

### 2. Add Site

1. Click "Add a Site"
2. Enter: **whodinees.com**
3. Select plan: **Free** (sufficient for now)
4. Click "Add Site"

### 3. DNS Configuration

Cloudflare will scan your existing DNS records. You'll see:

**Current DNS (Heroku):**
```
whodinees.com     CNAME   whodinees-8802a535baa6.herokuapp.com
www.whodinees.com CNAME   whodinees-8802a535baa6.herokuapp.com
```

**Actions:**
- ✅ Keep these records
- ✅ Enable "Proxied" (orange cloud) for both
- ✅ Add any missing records

### 4. Update Nameservers

Cloudflare will provide nameservers like:
```
aniyah.ns.cloudflare.com
dion.ns.cloudflare.com
```

**At your domain registrar** (where you bought whodinees.com):
1. Log in to your registrar
2. Find DNS/Nameserver settings
3. Replace existing nameservers with Cloudflare's
4. Save changes

**Propagation:** Takes 24-72 hours (usually faster)

### 5. SSL/TLS Settings

1. Go to SSL/TLS section
2. Set encryption mode: **Full (strict)**
   - Encrypts traffic between Cloudflare and Heroku
   - Verifies Heroku's SSL certificate
3. Enable "Always Use HTTPS"
4. Enable "Automatic HTTPS Rewrites"

### 6. Speed Optimizations

**Auto Minify:**
- ✅ JavaScript
- ✅ CSS
- ✅ HTML

**Brotli Compression:**
- ✅ Enable

**HTTP/3 (QUIC):**
- ✅ Enable

**Early Hints:**
- ✅ Enable (helps browser preload resources)

### 7. Caching Rules

**Browser Cache TTL:**
- Set to: **4 hours** (respects origin headers)

**Page Rules** (free plan: 3 rules max):

1. **Static Assets Rule:**
   - URL: `whodinees.com/static/*`
   - Settings:
     - Cache Level: Cache Everything
     - Edge Cache TTL: 1 month
     - Browser Cache TTL: 1 month

2. **API No-Cache Rule:**
   - URL: `whodinees.com/api/*`
   - Settings:
     - Cache Level: Bypass

3. **Media Files Rule:**
   - URL: `whodinees.com/media/*`
   - Settings:
     - Cache Level: Cache Everything
     - Edge Cache TTL: 1 week
     - Browser Cache TTL: 1 week

### 8. Security Settings

**Security Level:**
- Set to: **Medium** (balance between security and false positives)

**Challenge Passage:**
- Set to: **30 minutes** (how long visitors bypass challenges)

**Browser Integrity Check:**
- ✅ Enable (blocks known malicious browsers)

**Firewall Rules** (if needed):
- Block specific countries (if fraud detected)
- Rate limit aggressive scrapers beyond Django's rate limits
- Allow only specific IPs for admin panel (optional)

### 9. Analytics & Monitoring

**Web Analytics:**
- ✅ Enable Cloudflare Analytics (privacy-friendly)
- No need for client-side tracking code

**Bot Management:**
- View bot traffic in dashboard
- Free plan includes basic bot detection

### 10. Heroku Configuration

**Update Django settings** to trust Cloudflare IPs:

```python
# backend/whodinees/settings.py

# Trust Cloudflare proxy headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Already set, but verify:
ALLOWED_HOSTS = [
    'whodinees.com',
    'www.whodinees.com',
    'whodinees-8802a535baa6.herokuapp.com',
]
```

---

## Verification

After nameservers propagate:

1. **SSL Test:**
   ```bash
   curl -I https://whodinees.com
   ```
   Should return `200 OK` with `cf-ray` header

2. **CDN Test:**
   ```bash
   curl -I https://whodinees.com/static/favicon.svg
   ```
   Should show `cf-cache-status: HIT` on second request

3. **Performance Test:**
   - https://tools.pingdom.com
   - https://www.webpagetest.org
   - Should see faster load times from global locations

4. **Security Headers:**
   ```bash
   curl -I https://whodinees.com | grep -i cloudflare
   ```
   Should see `server: cloudflare`

---

## Troubleshooting

**"Too many redirects" error:**
- Check SSL/TLS mode is "Full (strict)"
- Verify Heroku app has SSL enabled

**Assets not caching:**
- Check Page Rules order (most specific first)
- Purge cache: Dashboard → Caching → Purge Everything

**Site not loading:**
- Verify nameservers updated correctly: `dig whodinees.com NS`
- Check Cloudflare status: https://www.cloudflarestatus.com

---

## Post-Setup Recommendations

1. **Set up Email Routing** (Cloudflare Email Routing - free):
   - Forward hello@whodinees.com → your personal email
   - No need for separate email hosting

2. **Monitor Analytics Weekly:**
   - Check for unusual traffic patterns
   - Review bot detection reports
   - Monitor cache hit ratio (aim for >90% on static assets)

3. **Upgrade to Pro if needed** ($20/mo):
   - Web Application Firewall (WAF)
   - More Page Rules (20 instead of 3)
   - Better DDoS protection
   - Priority support

4. **Test Disaster Recovery:**
   - Temporarily pause Cloudflare (grey cloud)
   - Verify site still works via Heroku direct

---

## Estimated Time

- Configuration: **30 minutes**
- Nameserver propagation: **1-24 hours**
- Full cache warm-up: **24-48 hours**

---

**Email for account:** hello@whodinees.com  
**Current Heroku URL:** whodinees-8802a535baa6.herokuapp.com
