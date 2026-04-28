"""
PDF invoice generation for portrait orders.

Uses wkhtmltopdf to convert HTML invoices to PDF.
"""
import os
import subprocess
import tempfile
from datetime import datetime
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def generate_invoice_pdf(order):
    """
    Generate a PDF invoice for a portrait order.
    
    Args:
        order: PortraitOrder instance
        
    Returns:
        bytes: PDF file content
        
    Raises:
        Exception: If PDF generation fails
    """
    # Render HTML invoice
    html_content = render_invoice_html(order)
    
    # Convert HTML to PDF using wkhtmltopdf
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
            html_file.write(html_content)
            html_path = html_file.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as pdf_file:
            pdf_path = pdf_file.name
        
        # Run wkhtmltopdf
        cmd = [
            'wkhtmltopdf',
            '--page-size', 'Letter',
            '--margin-top', '0.75in',
            '--margin-right', '0.75in',
            '--margin-bottom', '0.75in',
            '--margin-left', '0.75in',
            '--encoding', 'UTF-8',
            '--quiet',
            html_path,
            pdf_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        
        if result.returncode != 0:
            logger.error(f"wkhtmltopdf failed: {result.stderr.decode()}")
            raise Exception(f"PDF generation failed: {result.stderr.decode()}")
        
        # Read PDF content
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Cleanup temp files
        os.unlink(html_path)
        os.unlink(pdf_path)
        
        logger.info(f"Invoice PDF generated for order {order.id}: {len(pdf_content)} bytes")
        return pdf_content
        
    except subprocess.TimeoutExpired:
        logger.error("wkhtmltopdf timeout")
        raise Exception("PDF generation timeout")
    except Exception as e:
        logger.exception(f"Error generating invoice PDF: {e}")
        raise


def render_invoice_html(order):
    """
    Render HTML invoice template.
    
    Args:
        order: PortraitOrder instance
        
    Returns:
        str: HTML content
    """
    portrait = order.portrait
    
    # Get price breakdown
    breakdown = order.pricing_breakdown_json or {}
    
    # Format timestamp
    order_date = order.created_at.strftime("%B %d, %Y at %I:%M %p UTC")
    
    context = {
        'order': order,
        'portrait': portrait,
        'order_date': order_date,
        'breakdown': breakdown,
        'company_name': 'Mr. May Who LLC',
        'company_address': '123 Main St, Suite 100, San Francisco, CA 94105',  # TODO: Update with real address
        'company_email': 'hello@whodinees.com',
        'logo_url': 'https://whodinees.com/static/favicon.svg',  # TODO: Use actual logo
    }
    
    return render_to_string('portraits/invoice.html', context)


def save_invoice_to_order(order, pdf_content):
    """
    Save invoice PDF to order's media storage.
    
    Args:
        order: PortraitOrder instance
        pdf_content: bytes of PDF file
        
    Returns:
        str: Path to saved file
    """
    from django.core.files.base import ContentFile
    
    filename = f"invoice_order_{order.id}_{order.token}.pdf"
    
    # Save to order's invoice field
    # Note: Assumes PortraitOrder has an invoice FileField
    # Will add this in the next step
    order.invoice_pdf.save(filename, ContentFile(pdf_content), save=True)
    
    return order.invoice_pdf.url
