"""
Tests for Whodinees Portraits app
"""
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal
from .models import PetPortrait, PortraitOrder
from .services import metals_pricing, mesh_analyzer
import json


class PortraitAPITests(TestCase):
    """Test the portrait creation and workflow API"""
    
    def setUp(self):
        self.client = Client()
        # Create a minimal valid image
        self.test_image = SimpleUploadedFile(
            "test.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
    
    def test_health_check(self):
        """Ensure health endpoint works"""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('ok'))
    
    def test_create_portrait_requires_email(self):
        """Portrait creation should require email"""
        response = self.client.post('/api/portraits/', {
            'photo': self.test_image,
            'pet_type': 'dog'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_portrait_status_codes(self):
        """Check that status transitions work"""
        self.assertIn('photo_uploaded', dict(PetPortrait.STATUS_CHOICES))
        self.assertIn('deposit_pending', dict(PetPortrait.STATUS_CHOICES))
        self.assertIn('generating', dict(PetPortrait.STATUS_CHOICES))
        self.assertIn('awaiting_approval', dict(PetPortrait.STATUS_CHOICES))
        self.assertIn('approved', dict(PetPortrait.STATUS_CHOICES))


class PricingTests(TestCase):
    """Test pricing calculations"""
    
    def test_material_weight_calculation(self):
        """Volume to weight conversion should work"""
        volume_cm3 = 1.0  # 1 cubic cm
        
        # Silver should be heavy
        weight_silver = metals_pricing.calculate_material_weight(volume_cm3, 'silver')
        self.assertGreater(weight_silver, 10)  # Silver density ~10.36 g/cm³
        
        # Plastic should be light
        weight_plastic = metals_pricing.calculate_material_weight(volume_cm3, 'plastic')
        self.assertLess(weight_plastic, 2)  # Plastic density ~1.2 g/cm³
    
    def test_pricing_calculation_structure(self):
        """Pricing breakdown should have all required fields"""
        breakdown = metals_pricing.calculate_full_pricing(
            volume_cm3=0.85,
            polycount=20000,
            material='silver',
            shapeways_production_cost=48.00
        )
        
        # Check all required fields exist
        required_fields = [
            'material', 'volume_cm3', 'weight_grams', 'polycount',
            'complexity', 'spot_price_per_gram', 'material_cost',
            'shapeways_cost', 'design_fee', 'ai_processing_fee',
            'platform_fee', 'total'
        ]
        for field in required_fields:
            self.assertIn(field, breakdown, f"Missing field: {field}")
        
        # Check reasonable values
        self.assertGreater(breakdown['total'], 0)
        self.assertGreater(breakdown['weight_grams'], 0)
        self.assertEqual(breakdown['volume_cm3'], 0.85)
    
    def test_zero_volume_fallback(self):
        """Pricing should handle zero volume gracefully"""
        # Even with 0 volume, should return valid pricing (uses fallback)
        breakdown = metals_pricing.calculate_full_pricing(
            volume_cm3=0.0,
            polycount=20000,
            material='plastic',
            shapeways_production_cost=48.00
        )
        
        self.assertGreaterEqual(breakdown['total'], 0)
        # Plastic should use fixed cost
        self.assertEqual(breakdown['material_cost'], 2.00)
    
    def test_complexity_tiers(self):
        """Complexity should be auto-determined by polycount"""
        simple = metals_pricing.determine_complexity_tier(5000)
        moderate = metals_pricing.determine_complexity_tier(20000)
        complex_tier = metals_pricing.determine_complexity_tier(50000)
        
        self.assertEqual(simple, 'simple')
        self.assertEqual(moderate, 'moderate')
        self.assertEqual(complex_tier, 'complex')
        
        # Check design fees match
        self.assertEqual(metals_pricing.get_design_fee('simple'), 35)
        self.assertEqual(metals_pricing.get_design_fee('moderate'), 65)
        self.assertEqual(metals_pricing.get_design_fee('complex'), 95)


class WebhookTests(TestCase):
    """Test webhook handling"""
    
    def test_unified_webhook_endpoint_exists(self):
        """Unified webhook should be accessible"""
        response = self.client.post('/api/stripe/webhook/', 
            data=json.dumps({'type': 'ping'}),
            content_type='application/json'
        )
        # Should return 400 for invalid signature, not 404
        self.assertIn(response.status_code, [200, 400])
    
    def test_portrait_model_metadata_structure(self):
        """Portrait payment intent metadata should have required fields"""
        portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_type='dog',
            status='photo_uploaded'
        )
        
        from portraits.views import _pi_metadata
        metadata = _pi_metadata(portrait)
        
        self.assertIn('portrait_id', metadata)
        self.assertIn('portrait_token', metadata)
        self.assertIn('customer_email', metadata)
        self.assertIn('flow', metadata)
        self.assertEqual(metadata['flow'], 'portrait_deposit')


class MeshAnalyzerTests(TestCase):
    """Test mesh analysis fallbacks"""
    
    def test_fallback_volume_on_error(self):
        """Mesh analyzer should return fallback on error"""
        # Invalid URL should trigger exception path
        result = mesh_analyzer.analyze_glb('invalid://url')
        
        # Should return fallback structure
        self.assertIn('volume_cm3', result)
        self.assertIn('polycount', result)
        self.assertIn('error', result)
        
        # Fallback volume should be reasonable
        self.assertEqual(result['volume_cm3'], 0.85)
        self.assertEqual(result['polycount'], 20000)


class ModelTests(TestCase):
    """Test model constraints and validation"""
    
    def test_portrait_order_material_choices(self):
        """All material choices should be valid"""
        valid_materials = [choice[0] for choice in PortraitOrder.MATERIAL_CHOICES]
        
        # Check expected materials exist
        self.assertIn('plastic', valid_materials)
        self.assertIn('silver', valid_materials)
        self.assertIn('gold_14k_yellow', valid_materials)
        self.assertIn('platinum', valid_materials)
    
    def test_portrait_unique_token(self):
        """Each portrait should have a unique token"""
        p1 = PetPortrait.objects.create(
            customer_email='test1@example.com',
            pet_type='dog'
        )
        p2 = PetPortrait.objects.create(
            customer_email='test2@example.com',
            pet_type='cat'
        )
        
        self.assertNotEqual(p1.token, p2.token)
        self.assertIsNotNone(p1.token)
        self.assertIsNotNone(p2.token)
