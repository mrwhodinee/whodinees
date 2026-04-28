"""
SEO views: sitemap.xml, robots.txt, and meta tags
"""
from django.http import HttpResponse
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""
    priority = 0.8
    changefreq = 'weekly'

    def items(self):
        """Return list of static page names."""
        return [
            'spa',  # Homepage
            # Add other public pages here as they're created
        ]

    def location(self, item):
        """Return URL for each item."""
        if item == 'spa':
            return '/'
        return reverse(item)


def robots_txt(request):
    """
    Generate robots.txt
    
    Allows all bots to crawl the site and points to sitemap.
    """
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /api/",
        "",
        f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
