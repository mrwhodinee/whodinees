"""Instagram automation for Whodinees marketing.

Handles:
- OAuth authentication with Facebook
- Post scheduling and publishing
- Image uploads
- Caption generation
- Analytics tracking

Setup:
1. Create Facebook App at developers.facebook.com
2. Add Instagram Graph API product
3. Connect Instagram Business Account to Facebook Page
4. Set environment variables:
   - FACEBOOK_APP_ID
   - FACEBOOK_APP_SECRET
   - INSTAGRAM_ACCESS_TOKEN (long-lived, 60 days)
   - INSTAGRAM_ACCOUNT_ID
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v18.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class InstagramAPIError(Exception):
    """Instagram API request failed."""
    pass


def get_access_token() -> str:
    """Get Instagram access token from settings."""
    token = getattr(settings, 'INSTAGRAM_ACCESS_TOKEN', os.getenv('INSTAGRAM_ACCESS_TOKEN', ''))
    if not token:
        raise InstagramAPIError("INSTAGRAM_ACCESS_TOKEN not configured")
    return token


def get_account_id() -> str:
    """Get Instagram Business Account ID from settings."""
    account_id = getattr(settings, 'INSTAGRAM_ACCOUNT_ID', os.getenv('INSTAGRAM_ACCOUNT_ID', ''))
    if not account_id:
        raise InstagramAPIError("INSTAGRAM_ACCOUNT_ID not configured")
    return account_id


def api_request(endpoint: str, method: str = "GET", params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
    """Make authenticated request to Instagram Graph API.
    
    Args:
        endpoint: API endpoint (e.g., "/me" or "/12345/media")
        method: HTTP method
        params: Query parameters
        data: POST/PUT data
    
    Returns:
        JSON response dict
    
    Raises:
        InstagramAPIError: If request fails
    """
    url = f"{GRAPH_API_BASE}{endpoint}"
    params = params or {}
    params['access_token'] = get_access_token()
    
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            resp = requests.post(url, params=params, data=data, timeout=30)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        resp.raise_for_status()
        return resp.json()
    
    except requests.RequestException as e:
        logger.error(f"Instagram API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('error', {}).get('message', str(e))
            except:
                error_msg = str(e)
        else:
            error_msg = str(e)
        raise InstagramAPIError(f"API request failed: {error_msg}")


def publish_photo(image_url: str, caption: str, location_id: Optional[str] = None) -> str:
    """Publish a photo to Instagram.
    
    Two-step process:
    1. Create media container
    2. Publish the container
    
    Args:
        image_url: Publicly accessible image URL (HTTPS required)
        caption: Post caption (max 2200 chars)
        location_id: Optional Instagram location ID
    
    Returns:
        Instagram media ID of published post
    
    Raises:
        InstagramAPIError: If publishing fails
    """
    account_id = get_account_id()
    
    # Step 1: Create media container
    container_data = {
        'image_url': image_url,
        'caption': caption[:2200],  # Instagram limit
    }
    if location_id:
        container_data['location_id'] = location_id
    
    logger.info(f"Creating Instagram media container for image: {image_url}")
    container_resp = api_request(f"/{account_id}/media", method="POST", data=container_data)
    creation_id = container_resp.get('id')
    
    if not creation_id:
        raise InstagramAPIError("No creation ID returned from container creation")
    
    # Step 2: Publish the container
    logger.info(f"Publishing Instagram media container: {creation_id}")
    publish_resp = api_request(f"/{account_id}/media_publish", method="POST", data={'creation_id': creation_id})
    media_id = publish_resp.get('id')
    
    if not media_id:
        raise InstagramAPIError("No media ID returned from publish")
    
    logger.info(f"Successfully published Instagram post: {media_id}")
    return media_id


def get_account_info() -> Dict:
    """Get Instagram Business Account info.
    
    Returns:
        Account data including username, profile pic, followers, etc.
    """
    account_id = get_account_id()
    fields = "id,username,name,profile_picture_url,followers_count,follows_count,media_count"
    return api_request(f"/{account_id}", params={'fields': fields})


def get_media_insights(media_id: str) -> Dict:
    """Get insights for a published media item.
    
    Args:
        media_id: Instagram media ID
    
    Returns:
        Insights data (impressions, reach, engagement, etc.)
    """
    metrics = "engagement,impressions,reach,saved,likes,comments,shares"
    return api_request(f"/{media_id}/insights", params={'metric': metrics})


def test_connection() -> bool:
    """Test Instagram API connection and credentials.
    
    Returns:
        True if connection works, False otherwise
    """
    try:
        info = get_account_info()
        logger.info(f"Instagram connection test successful: @{info.get('username')}")
        return True
    except Exception as e:
        logger.error(f"Instagram connection test failed: {e}")
        return False


# Content generation helpers

def generate_pet_portrait_caption(pet_name: str, material: str, spot_price: float) -> str:
    """Generate caption for a pet portrait post.
    
    Args:
        pet_name: Name of the pet
        material: Material name (e.g., "sterling silver", "14K gold")
        spot_price: Current spot price per gram
    
    Returns:
        Instagram caption
    """
    captions = [
        f"Meet {pet_name} — immortalized in {material}. 🐾✨\n\n"
        f"From your photo to precious metal. Live spot pricing at ${spot_price}/g.\n"
        f"This isn't a gift — it's an investment piece.\n\n"
        f"Upload your pet's photo → We generate a 3D model → Choose your metal → It's yours forever.\n\n"
        f"Link in bio to start your portrait. 💎",
        
        f"Your pet. In {material}. Priced at today's market rate.\n\n"
        f"{pet_name} is now a {material} sculpture valued at live spot prices (${spot_price}/g).\n\n"
        f"We don't guess the price — we calculate from your actual 3D model weight.\n"
        f"Full transparent breakdown. No markup games.\n\n"
        f"This is how jewelry should be priced. And now, your pet.\n\n"
        f"whodinees.com 🐕",
        
        f"Not a tchotchke. An heirloom.\n\n"
        f"{pet_name} in {material}. Custom 3D printed from your photo.\n"
        f"Live precious metal pricing: ${spot_price}/gram today.\n\n"
        f"$19 gets you the 3D model (you keep the files).\n"
        f"Then choose: plastic, silver, gold, or platinum.\n\n"
        f"The metal value is real. The pricing is transparent.\n"
        f"The piece is forever.\n\n"
        f"Link in bio. 🪙"
    ]
    
    import random
    return random.choice(captions)
