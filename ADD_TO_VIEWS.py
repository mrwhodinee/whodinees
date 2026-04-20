"""
Add these functions to portraits/views.py after the pricing_view function:
"""

@api_view(["POST"])
@permission_classes([AllowAny])
def calculate_portrait_price(request, portrait_id: int):
    """POST /api/portraits/:id/calculate-price
    
    Calculate live pricing for a specific portrait + material.
    Body: {"material": "silver"}
    """
    try:
        portrait = PetPortrait.objects.get(pk=portrait_id)
    except PetPortrait.DoesNotExist:
        return Response({"detail": "Not found"}, status=404)
    
    if not portrait.selected_variant_task_id:
        return Response({"detail": "No variant selected"}, status=400)
    
    # Get GLB URL from selected variant
    selected = next(
        (v for v in portrait.meshy_variants if v.get("task_id") == portrait.selected_variant_task_id),
        None
    )
    if not selected or not selected.get("glb_url"):
        return Response({"detail": "GLB not available"}, status=400)
    
    material = request.data.get("material", "silver")
    if material not in dict(PortraitOrder.MATERIAL_CHOICES):
        return Response({"detail": "Invalid material"}, status=400)
    
    # Calculate pricing using actual model
    from .services import pricing as pricing_service
    try:
        breakdown = pricing_service.compute_price_for_model(
            glb_url=selected["glb_url"],
            material=material,
            shapeways_cost=48.00,  # TODO: Get real Shapeways quote
        )
        return Response(breakdown)
    except Exception as e:
        logger.exception("Pricing calculation failed")
        return Response({"detail": str(e)}, status=500)
