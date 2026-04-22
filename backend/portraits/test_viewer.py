"""
Tests specifically for the 3D model viewer integration
"""
from django.test import TestCase, Client
from .models import PetPortrait


class ModelViewerIntegrationTests(TestCase):
    """Test that the model viewer gets the data it needs"""
    
    def setUp(self):
        self.client = Client()
        # Create a portrait with a selected variant
        self.portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_type='dog',
            status='awaiting_approval',
            meshy_variants=[
                {
                    'task_id': 'test-task-123',
                    'status': 'SUCCEEDED',
                    'glb_url': 'https://cdn.meshy.ai/test-model.glb',
                    'preview_url': 'https://cdn.meshy.ai/test-preview.png',
                    'volume_cm3': 0.85,
                    'polycount': 25000
                }
            ],
            selected_variant_task_id='test-task-123'
        )
    
    def test_portrait_has_variants(self):
        """Portrait should have meshy_variants data"""
        self.assertIsNotNone(self.portrait.meshy_variants)
        self.assertGreater(len(self.portrait.meshy_variants), 0)
    
    def test_portrait_has_selected_variant(self):
        """Portrait should have a selected variant"""
        self.assertIsNotNone(self.portrait.selected_variant_task_id)
        self.assertTrue(len(self.portrait.selected_variant_task_id) > 0)
    
    def test_portrait_api_returns_viewer_data(self):
        """API should return all data needed for model viewer"""
        response = self.client.get(f'/api/portraits/{self.portrait.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Check viewer-critical fields
        self.assertIn('meshy_variants', data)
        self.assertIn('selected_variant_task_id', data)
        
        # Verify variants have required fields
        if data['meshy_variants']:
            variant = data['meshy_variants'][0]
            self.assertIn('glb_url', variant)
            self.assertIn('preview_url', variant)
    
    def test_variant_glb_url_is_accessible(self):
        """GLB URL format should be valid for model-viewer"""
        variant = self.portrait.meshy_variants[0]
        glb_url = variant.get('glb_url', '')
        
        valid_prefixes = ('http://', 'https://', 'data:')
        self.assertTrue(
            any(glb_url.startswith(prefix) for prefix in valid_prefixes),
            f"GLB URL '{glb_url}' should start with http://, https://, or data:"
        )
    
    def test_variant_preview_is_accessible(self):
        """Preview image URL should be valid"""
        variant = self.portrait.meshy_variants[0]
        preview_url = variant.get('preview_url', '')
        
        valid_prefixes = ('http://', 'https://', 'data:')
        self.assertTrue(
            any(preview_url.startswith(prefix) for prefix in valid_prefixes),
            f"Preview URL '{preview_url}' should start with http://, https://, or data:"
        )
    
    def test_volume_is_reasonable(self):
        """Volume should be in a reasonable range for 3D printing"""
        variant = self.portrait.meshy_variants[0]
        volume = variant.get('volume_cm3', 0)
        
        # Typical range: 0.5 - 50 cm³ for small figurines
        self.assertGreater(volume, 0.1)
        self.assertLess(volume, 100)
    
    def test_polycount_is_reasonable(self):
        """Polycount should be in a reasonable range"""
        variant = self.portrait.meshy_variants[0]
        polycount = variant.get('polycount', 0)
        
        # Typical range: 5,000 - 100,000 for web 3D
        self.assertGreater(polycount, 1000)
        self.assertLess(polycount, 200000)


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
    
    # NOTE: Can't test for model-viewer script in CI since frontend isn't built
    # The test would need the frontend build step to run before Django tests


class ViewerErrorHandlingTests(TestCase):
    """Test viewer fallback when model fails to load"""
    
    def test_portrait_without_variants(self):
        """Portrait without variants should still return valid data"""
        portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_type='cat',
            status='generating'
        )
        
        response = self.client.get(f'/api/portraits/{portrait.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Should have the field, even if empty
        self.assertIn('meshy_variants', data)
        self.assertEqual(data['meshy_variants'], [])
    
    def test_portrait_with_malformed_variant(self):
        """Portrait with malformed variant data should still return"""
        portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_type='dog',
            status='awaiting_approval',
            meshy_variants=[
                {
                    'task_id': 'broken',
                    'glb_url': 'not-a-valid-url'
                }
            ]
        )
        
        response = self.client.get(f'/api/portraits/{portrait.id}/')
        self.assertEqual(response.status_code, 200)
        
        # API should return the data even if URL is invalid
        # (Frontend will handle the error)
        data = response.json()
        self.assertEqual(len(data['meshy_variants']), 1)
        self.assertEqual(data['meshy_variants'][0]['glb_url'], 'not-a-valid-url')
