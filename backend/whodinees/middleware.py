"""
Custom middleware for Whodinees.
"""


class SecurityHeadersMiddleware:
    """
    Add security and cache headers for production.
    
    Cloudflare will respect these headers when proxying.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Security headers (defense in depth; Cloudflare also adds some)
        if not response.get('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'
        
        if not response.get('X-Frame-Options'):
            response['X-Frame-Options'] = 'DENY'
        
        if not response.get('Referrer-Policy'):
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Cache control for API responses (don't cache by default)
        if request.path.startswith('/api/'):
            if not response.get('Cache-Control'):
                response['Cache-Control'] = 'private, no-cache, no-store, must-revalidate'
        
        # Long cache for static assets
        if request.path.startswith('/static/'):
            if not response.get('Cache-Control'):
                # 1 year cache (static files are versioned/hashed)
                response['Cache-Control'] = 'public, max-age=31536000, immutable'
        
        # Medium cache for media uploads (user photos, generated models)
        if request.path.startswith('/media/'):
            if not response.get('Cache-Control'):
                # 1 week cache for media
                response['Cache-Control'] = 'public, max-age=604800'
        
        return response
