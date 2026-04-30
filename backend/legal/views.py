from django.shortcuts import render


def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'legal/privacy_policy.html')


def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'legal/terms_of_service.html')


def refund_policy(request):
    """Refund and Return Policy page"""
    return render(request, 'legal/refund_policy.html')
