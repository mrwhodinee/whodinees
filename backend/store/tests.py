"""
Tests for Whodinees Store app
"""
from django.test import TestCase, Client
from .models import Product, Category, Order, OrderItem
from decimal import Decimal


class StoreAPITests(TestCase):
    """Test store API endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category',
            live=True
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('29.99'),
            description='Test description',
            in_stock=True
        )
    
    def test_health_endpoint(self):
        """Health check should return OK"""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertIn('products', data)
    
    def test_product_list(self):
        """Product list should return products"""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['slug'], 'test-product')
    
    def test_product_detail(self):
        """Product detail should return single product"""
        response = self.client.get(f'/api/products/{self.product.slug}/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], 'Test Product')
        self.assertEqual(data['price'], '29.99')
    
    def test_category_list(self):
        """Category list should return categories"""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
    
    def test_category_filter_live_only(self):
        """Category list should filter by live=true"""
        # Create a non-live category
        Category.objects.create(
            name='Hidden Category',
            slug='hidden',
            live=False
        )
        
        response = self.client.get('/api/categories/?live=true')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should only return live categories
        for cat in data:
            self.assertTrue(cat.get('live', False))


class OrderModelTests(TestCase):
    """Test Order model functionality"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Test',
            slug='test',
            live=True
        )
        self.product = Product.objects.create(
            name='Test Product',
            slug='test-product',
            category=self.category,
            price=Decimal('50.00'),
            in_stock=True
        )
    
    def test_order_creation(self):
        """Order should be created with proper defaults"""
        order = Order.objects.create(
            customer_name='Test Customer',
            customer_email='test@example.com',
            shipping_line1='123 Test St',
            shipping_city='Test City',
            shipping_postal_code='12345',
            shipping_country='US'
        )
        
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.currency, 'usd')
        self.assertIsNotNone(order.token)
    
    def test_order_total_computation(self):
        """Order should compute totals correctly"""
        order = Order.objects.create(
            customer_name='Test',
            customer_email='test@example.com',
            shipping_line1='123 Test',
            shipping_city='City',
            shipping_postal_code='12345',
            shipping_country='US'
        )
        
        # Add order item
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            unit_price_snapshot=self.product.price
        )
        
        order.recompute_totals()
        
        # 2 items × $50 = $100 subtotal
        self.assertEqual(order.subtotal, Decimal('100.00'))
        # $100 + $6 shipping = $106 total
        self.assertEqual(order.shipping_cost, Decimal('6.00'))
        self.assertEqual(order.total, Decimal('106.00'))


class WebhookIntegrationTests(TestCase):
    """Test webhook integration points"""
    
    def test_webhook_endpoint_accessible(self):
        """Webhook endpoint should be accessible"""
        response = self.client.post('/api/stripe/webhook/', 
            data='{"type": "test"}',
            content_type='application/json'
        )
        # Should return 400 for bad signature, not 404
        self.assertIn(response.status_code, [200, 400])
    
    def test_stripe_config_present(self):
        """Stripe configuration should be loadable"""
        from django.conf import settings
        
        # Keys should exist (even if empty in test)
        self.assertTrue(hasattr(settings, 'STRIPE_PUBLISHABLE_KEY'))
        self.assertTrue(hasattr(settings, 'STRIPE_SECRET_KEY'))
        self.assertTrue(hasattr(settings, 'STRIPE_WEBHOOK_SECRET'))


class SPARoutingTests(TestCase):
    """Test SPA routing and static file serving"""
    
    def test_spa_index_for_unknown_routes(self):
        """Unknown routes should return SPA index"""
        # API routes should 404
        response = self.client.get('/api/nonexistent/')
        self.assertEqual(response.status_code, 404)
        
        # Frontend routes should return HTML
        response = self.client.get('/some-random-page/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])
