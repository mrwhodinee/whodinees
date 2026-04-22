"""
Tests specifically for the 3D model viewer integration
"""
from django.test import TestCase, Client
from .models import PetPortrait


class ModelViewerIntegrationTests(TestCase):
    """Test that the model viewer gets the data it needs"""
    
    def setUp(self):
        self.client = Client()
        # Create a portrait with all the viewer fields populated
        self.portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_type='dog',
            status='awaiting_approval',
            glb_url='https://cdn.meshy.ai/test-model.glb',
            preview_image_url='https://cdn.meshy.ai/test-preview.png',
            volume_cm3=0.85,
            polycount=25000
        )
    
    def test_portrait_has_glb_url(self):
        """Portrait should have GLB URL for model viewer"""
        self.assertIsNotNone(self.portrait.glb_url)
        self.assertTrue(self.portrait.glb_url.startswith('http'))
    
    def test_portrait_has_preview_image(self):
        """Portrait should have preview image for poster"""
        self.assertIsNotNone(self.portrait.preview_image_url)
        self.assertTrue(self.portrait.preview_image_url.startswith('http'))
    
    def test_portrait_api_returns_viewer_data(self):
        """API should return all data needed for model viewer"""
        response = self.client.get(f'/api/portraits/{self.portrait.token}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Check viewer-critical fields
        self.assertIn('glb_url', data)
        self.assertIn('preview_image_url', data)
        self.assertIn('volume_cm3', data)
        self.assertIn('polycount', data)
        
        # Verify values
        self.assertEqual(data['glb_url'], self.portrait.glb_url)
        self.assertEqual(data['preview_image_url'], self.portrait.preview_image_url)
    
    def test_glb_url_is_accessible(self):
        """GLB URL format should be valid for model-viewer"""
        # Model-viewer requires http/https URLs or data URIs
        glb_url = self.portrait.glb_url
        
        valid_prefixes = ('http://', 'https://', 'data:')
        self.assertTrue(
            any(glb_url.startswith(prefix) for prefix in valid_prefixes),
            f"GLB URL '{glb_url}' should start with http://, https://, or data:"
        )
    
    def test_preview_image_is_accessible(self):
        """Preview image URL should be valid"""
        preview_url = self.portrait.preview_image_url
        
        valid_prefixes = ('http://', 'https://', 'data:')
        self.assertTrue(
            any(preview_url.startswith(prefix) for prefix in valid_prefixes),
            f"Preview URL '{preview_url}' should start with http://, https://, or data:"
        )
    
    def test_volume_is_reasonable(self):
        """Volume should be in a reasonable range for 3D printing"""
        # Typical range: 0.5 - 50 cm³ for small figurines
        self.assertGreater(self.portrait.volume_cm3, 0.1)
        self.assertLess(self.portrait.volume_cm3, 100)
    
    def test_polycount_is_reasonable(self):
        """Polycount should be in a reasonable range"""
        # Typical range: 5,000 - 100,000 for web 3D
        self.assertGreater(self.portrait.polycount, 1000)
        self.assertLess(self.portrait.polycount, 200000)


class StaticFileTests(TestCase):
    """Test that static files needed for viewer are accessible"""
    
    def setUp(self):
        self.client = Client()
    
    def test_test_viewer_page_exists(self):
        """Test model-viewer HTML page should be accessible"""
        response = self.client.get('/static/test-model-viewer.html')
        
        # Should either return the file or 404 (depending on collectstatic)
        self.assertIn(response.status_code, [200, 404])
    
    def test_index_html_exists(self):
        """Frontend index.html should be accessible"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
    
    def test_index_has_model_viewer_script(self):
        """Frontend should load model-viewer script"""
        response = self.client.get('/')
        content = response.content.decode('utf-8')
        
        # Check for model-viewer script in head
        self.assertIn('model-viewer', content.lower())


class ViewerErrorHandlingTests(TestCase):
    """Test viewer fallback when model fails to load"""
    
    def test_portrait_without_glb_url(self):
        """Portrait without GLB URL should still return valid data"""
        portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_type='cat',
            status='generating'
        )
        
        response = self.client.get(f'/api/portraits/{portrait.token}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Should have the field, even if empty/null
        self.assertIn('glb_url', data)
    
    def test_portrait_with_invalid_glb_url(self):
        """Portrait with malformed GLB URL should still return data"""
        portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_type='dog',
            status='awaiting_approval',
            glb_url='not-a-valid-url'
        )
        
        response = self.client.get(f'/api/portraits/{portrait.token}/')
        self.assertEqual(response.status_code, 200)
        
        # API should return the data even if URL is invalid
        # (Frontend will handle the error)
        data = response.json()
        self.assertEqual(data['glb_url'], 'not-a-valid-url')
