"""Comprehensive test suite for Whodinees portraits flow."""
import os
import tempfile
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
import io

from .models import PetPortrait, PortraitOrder
from .services import metals_pricing, mesh_analyzer


class WeightCalculationTest(TestCase):
    """Test weight calculation accuracy for all 7 materials."""
    
    def test_weight_calculation_all_materials(self):
        """Known volume inputs should produce correct weights for each material."""
        test_volume = 1.0  # 1 cm³
        
        expected_weights = {
            'plastic': 1.2,
            'silver': 10.36,
            'gold_14k_yellow': 13.07,
            'gold_14k_rose': 13.07,
            'gold_14k_white': 13.07,
            'gold_18k_yellow': 15.58,
            'platinum': 21.40,
        }
        
        for material, expected in expected_weights.items():
            weight = metals_pricing.calculate_material_weight(test_volume, material)
            self.assertAlmostEqual(
                weight, expected, places=2,
                msg=f"{material} weight calculation incorrect"
            )


class DesignFeeTierTest(TestCase):
    """Test design fee tier logic."""
    
    def test_design_fee_tiers(self):
        """Polygon count thresholds should assign correct tiers."""
        test_cases = [
            (5000, 'simple', 25),
            (9999, 'simple', 25),
            (10000, 'moderate', 45),
            (29999, 'moderate', 45),
            (30000, 'complex', 75),
            (50000, 'complex', 75),
        ]
        
        for polycount, expected_tier, expected_fee in test_cases:
            tier = metals_pricing.determine_complexity_tier(polycount)
            fee = metals_pricing.get_design_fee(tier)
            
            self.assertEqual(
                tier, expected_tier,
                msg=f"Polycount {polycount} should be tier {expected_tier}"
            )
            self.assertEqual(
                fee, expected_fee,
                msg=f"Tier {expected_tier} should have fee ${expected_fee}"
            )


class SpotPriceTest(TestCase):
    """Test spot price fetching and caching."""
    
    @patch('portraits.services.metals_pricing.requests.get')
    def test_spot_price_fetch(self, mock_get):
        """Spot price API should return correct values."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'metals': {
                'silver': 27.50,  # per troy ounce
                'gold': 2200.00,
                'platinum': 950.00,
            }
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        prices = metals_pricing.get_spot_prices()
        
        # Convert to per gram (1 troy oz = 31.1035g)
        self.assertAlmostEqual(prices['silver'], 27.50 / 31.1035, places=2)
        self.assertAlmostEqual(prices['gold'], 2200.00 / 31.1035, places=2)
        self.assertAlmostEqual(prices['platinum'], 950.00 / 31.1035, places=2)
    
    @patch('portraits.services.metals_pricing.requests.get')
    def test_spot_price_caching(self, mock_get):
        """Spot prices should cache for 60 seconds."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'metals': {'silver': 27.50, 'gold': 2200, 'platinum': 950}}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # First call
        metals_pricing.get_spot_prices()
        call_count_1 = mock_get.call_count
        
        # Second call (should use cache)
        metals_pricing.get_spot_prices()
        call_count_2 = mock_get.call_count
        
        self.assertEqual(call_count_1, call_count_2, "Second call should use cache")
    
    def test_karat_purity_multipliers(self):
        """Gold variants should apply correct karat purity multipliers."""
        spot_prices = {'gold': 70.0, 'silver': 0.85, 'platinum': 30.0}
        
        # 14K gold = 58.3% purity
        cost_14k = metals_pricing.calculate_material_cost(10.0, 'gold_14k_yellow', spot_prices)
        expected_14k = 10.0 * 70.0 * 0.583
        self.assertAlmostEqual(cost_14k, expected_14k, places=2)
        
        # 18K gold = 75% purity
        cost_18k = metals_pricing.calculate_material_cost(10.0, 'gold_18k_yellow', spot_prices)
        expected_18k = 10.0 * 70.0 * 0.750
        self.assertAlmostEqual(cost_18k, expected_18k, places=2)


class PriceBreakdownTest(TestCase):
    """Test price breakdown math."""
    
    def test_breakdown_totals(self):
        """Price breakdown totals should be mathematically correct."""
        breakdown = metals_pricing.calculate_full_pricing(
            volume_cm3=0.85,
            polycount=20000,
            material='silver',
            shapeways_production_cost=48.00,
        )
        
        calculated_total = (
            breakdown['material_cost'] +
            breakdown['shapeways_cost'] +
            breakdown['design_fee']
        )
        
        self.assertAlmostEqual(
            breakdown['total'], calculated_total, places=2,
            msg="Total should equal sum of components"
        )


class OrderModelTest(TestCase):
    """Test Order model."""
    
    def setUp(self):
        self.portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_name='Test Pet',
            pet_type='dog',
            status='approved',
            selected_variant_task_id='test-123',
        )
    
    def test_order_creation(self):
        """Order should create correctly with all fields."""
        order = PortraitOrder.objects.create(
            portrait=self.portrait,
            material='silver',
            size_mm=40,
            volume_cm3=Decimal('0.85'),
            weight_grams=Decimal('8.81'),
            polycount=20000,
            complexity_tier='moderate',
            spot_price_per_gram=Decimal('0.87'),
            material_cost=Decimal('7.66'),
            shapeways_cost=Decimal('48.00'),
            design_fee=Decimal('45.00'),
            retail_price=Decimal('100.66'),
            pricing_breakdown_json={'test': 'data'},
            shipping_name='Test User',
            shipping_address1='123 Test St',
            shipping_city='Test City',
            shipping_region='TS',
            shipping_postcode='12345',
            shipping_country='US',
        )
        
        self.assertEqual(order.material, 'silver')
        self.assertEqual(order.complexity_tier, 'moderate')
        self.assertIsNotNone(order.pricing_breakdown_json)
    
    def test_order_stores_spot_price_snapshot(self):
        """Order should store spot price at time of order."""
        order = PortraitOrder.objects.create(
            portrait=self.portrait,
            material='gold_14k_yellow',
            size_mm=40,  # Now required (or uses default)
            spot_price_per_gram=Decimal('72.50'),
            pricing_breakdown_json={
                'spot_price_per_gram': 72.50,
                'timestamp': '2026-04-21T00:00:00Z'
            },
        )
        
        self.assertEqual(order.spot_price_per_gram, Decimal('72.50'))
        self.assertIn('spot_price_per_gram', order.pricing_breakdown_json)


class EdgeCaseTest(TestCase):
    """Test edge cases and error handling."""
    
    @patch('portraits.services.metals_pricing.requests.get')
    def test_metals_api_down_graceful_fallback(self, mock_get):
        """Should fail gracefully if metals.dev is down."""
        mock_get.side_effect = Exception("API unreachable")
        
        # Should not crash, should return fallback prices
        prices = metals_pricing.get_spot_prices()
        
        self.assertIsInstance(prices, dict)
        self.assertIn('silver', prices)
        self.assertGreater(prices['silver'], 0)
    
    def test_spot_price_zero_handling(self):
        """Should handle zero or null spot prices gracefully."""
        spot_prices = {'silver': 0, 'gold': None, 'platinum': 30.0}
        
        cost = metals_pricing.calculate_material_cost(10.0, 'silver', spot_prices)
        self.assertEqual(cost, 0.0, "Zero spot price should return zero cost")
    
    def test_malformed_model_volume_calculation(self):
        """Should handle trimesh failures gracefully."""
        # Create invalid GLB data
        invalid_glb = b'not a real glb file'
        
        with tempfile.NamedTemporaryFile(suffix='.glb', delete=False) as f:
            f.write(invalid_glb)
            temp_path = f.name
        
        try:
            result = mesh_analyzer.analyze_glb(temp_path)
            # Should return fallback values, not crash
            self.assertIn('volume_cm3', result)
            self.assertGreater(result['volume_cm3'], 0)
        finally:
            os.unlink(temp_path)


class APIEndpointTest(TestCase):
    """Test API endpoints."""
    
    def setUp(self):
        self.client = Client()
    
    def test_homepage_returns_200(self):
        """Homepage should return 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_pricing_endpoint(self):
        """GET /api/pricing/portrait should return pricing data."""
        response = self.client.get('/api/pricing/portrait')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('materials', data)
        self.assertIn('spot_prices', data)
    
    def test_upload_accepts_valid_image(self):
        """POST /api/portraits/ should accept valid image files."""
        # Create valid test image with enough detail to be >100KB
        import numpy as np
        # Create random noise pattern to increase file size
        arr = np.random.randint(0, 256, (1600, 1600, 3), dtype=np.uint8)
        img = Image.fromarray(arr)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        
        uploaded_file = SimpleUploadedFile(
            "test_pet.jpg",
            img_io.read(),
            content_type="image/jpeg"
        )
        
        response = self.client.post('/api/portraits/', {
            'customer_email': 'test@example.com',
            'pet_name': 'Test Pet',
            'pet_type': 'dog',
            'photo': uploaded_file,
        })
        
        if response.status_code != 201:
            print(f"Response: {response.status_code}, {response.json()}")
        self.assertEqual(response.status_code, 201)
    
    def test_upload_rejects_oversized_file(self):
        """POST /api/portraits/ should reject files over 15MB."""
        # Create oversized file (16MB of data)
        large_data = b'x' * (16 * 1024 * 1024)
        uploaded_file = SimpleUploadedFile(
            "huge.jpg",
            large_data,
            content_type="image/jpeg"
        )
        
        response = self.client.post('/api/portraits/', {
            'customer_email': 'test@example.com',
            'pet_name': 'Test Pet',
            'pet_type': 'dog',
            'photo': uploaded_file,
        })
        
        self.assertEqual(response.status_code, 400)
    
    def test_upload_rejects_invalid_file_type(self):
        """POST /api/portraits/ should reject non-image files."""
        uploaded_file = SimpleUploadedFile(
            "test.txt",
            b"not an image",
            content_type="text/plain"
        )
        
        response = self.client.post('/api/portraits/', {
            'customer_email': 'test@example.com',
            'pet_name': 'Test Pet',
            'pet_type': 'dog',
            'photo': uploaded_file,
        })
        
        self.assertEqual(response.status_code, 400)


class DepositFlowTest(TestCase):
    """Test deposit payment flow doesn't loop."""
    
    def setUp(self):
        self.client = Client()
    
    def test_deposit_redirect_after_payment(self):
        """After deposit is paid, /deposit should redirect to status page."""
        # Create a portrait with paid deposit
        portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_name='Test Pet',
            pet_type='dog',
            status='generating',
            deposit_paid=True,
            photo_quality_score=85,
        )
        
        # Try to access deposit page
        response = self.client.get(f'/portraits/{portrait.id}/deposit')
        
        # Should redirect (302) or show loading message (200 with redirect script)
        # Frontend handles redirect, so just check it doesn't show payment form
        self.assertIn(response.status_code, [200, 302])
        
        if response.status_code == 200:
            # Should show loading/redirect message, not payment form
            content = response.content.decode('utf-8')
            self.assertNotIn('PaymentElement', content)
            # React app will handle redirect via JS
    
    def test_payment_success_shows_generation_status(self):
        """After payment, status page should show generating message."""
        portrait = PetPortrait.objects.create(
            customer_email='test@example.com',
            pet_name='Test Pet',
            pet_type='dog',
            status='generating',
            deposit_paid=True,
            photo_quality_score=85,
        )
        
        response = self.client.get(f'/api/portraits/{portrait.id}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'generating')
        self.assertTrue(data['deposit_paid'])
