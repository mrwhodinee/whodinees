"""Order status portal views for customers."""
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, FileResponse
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PetPortrait, PortraitOrder


def order_status_lookup(request):
    """Lookup page: enter email to find your orders."""
    return render(request, 'portraits/order_status_lookup.html')


@api_view(['POST'])
def find_orders_by_email(request):
    """API endpoint: find all orders for a given email."""
    email = request.data.get('email', '').strip().lower()
    
    if not email:
        return Response({'error': 'Email is required'}, status=400)
    
    # Find all portraits for this email
    portraits = PetPortrait.objects.filter(
        customer_email__iexact=email
    ).prefetch_related('orders').order_by('-created_at')
    
    if not portraits.exists():
        return Response({'orders': []})
    
    orders_data = []
    for portrait in portraits:
        portrait_data = {
            'portrait_id': portrait.id,
            'token': str(portrait.token),
            'pet_name': portrait.pet_name,
            'pet_type': portrait.get_pet_type_display(),
            'status': portrait.get_status_display(),
            'created_at': portrait.created_at.isoformat(),
            'orders': []
        }
        
        for order in portrait.orders.all():
            portrait_data['orders'].append({
                'order_id': order.id,
                'token': str(order.token),
                'material': order.get_material_display(),
                'size_mm': order.size_mm,
                'price': float(order.retail_price),
                'status': order.get_status_display(),
                'tracking_number': order.tracking_number,
                'created_at': order.created_at.isoformat(),
                'has_invoice': bool(order.invoice_pdf),
                'has_glb': bool(portrait.selected_variant_task_id),
            })
        
        orders_data.append(portrait_data)
    
    return Response({'orders': orders_data})


def order_detail(request, order_token):
    """Detailed order status page."""
    order = get_object_or_404(PortraitOrder, token=order_token)
    
    # Get the selected GLB URL if available
    glb_url = None
    if order.portrait.selected_variant_task_id:
        for variant in order.portrait.meshy_variants:
            if variant.get('task_id') == order.portrait.selected_variant_task_id:
                glb_url = variant.get('glb_url')
                break
    
    context = {
        'order': order,
        'portrait': order.portrait,
        'glb_url': glb_url,
    }
    
    return render(request, 'portraits/order_detail.html', context)


def download_invoice(request, order_token):
    """Download PDF invoice for an order."""
    order = get_object_or_404(PortraitOrder, token=order_token)
    
    if not order.invoice_pdf:
        raise Http404("Invoice not available")
    
    return FileResponse(
        order.invoice_pdf.open('rb'),
        as_attachment=True,
        filename=f'Whodinees_Invoice_{order.id}.pdf'
    )


def download_model(request, portrait_token):
    """Download GLB model for an approved portrait."""
    portrait = get_object_or_404(PetPortrait, token=portrait_token)
    
    if not portrait.selected_variant_task_id:
        raise Http404("No model selected")
    
    # Find the selected variant
    glb_url = None
    for variant in portrait.meshy_variants:
        if variant.get('task_id') == portrait.selected_variant_task_id:
            glb_url = variant.get('glb_url')
            break
    
    if not glb_url:
        raise Http404("Model not available")
    
    # Proxy the GLB from Meshy
    import requests
    response = requests.get(glb_url, stream=True)
    
    if response.status_code != 200:
        raise Http404("Model download failed")
    
    # Stream the GLB file
    file_response = HttpResponse(
        response.iter_content(chunk_size=8192),
        content_type='model/gltf-binary'
    )
    file_response['Content-Disposition'] = f'attachment; filename="whodinees_{portrait.pet_name or portrait.id}.glb"'
    
    return file_response
