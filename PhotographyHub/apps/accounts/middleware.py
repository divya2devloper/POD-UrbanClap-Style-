from django.shortcuts import redirect
from django.urls import reverse

class WhatsAppRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # List of URLs that don't require the middleware check
            exempt_urls = [
                reverse('whatsapp-setup'),
                reverse('account_logout'),
                '/admin/',
            ]
            
            current_path = request.path
            is_exempt = any(current_path.startswith(url) for url in exempt_urls)
            
            # Check if user has a profile and if the whatsapp number is missing
            try:
                profile = request.user.profile
                if not profile.whatsapp_number and not is_exempt:
                    return redirect(f"{reverse('whatsapp-setup')}?next={current_path}")
            except AttributeError:
                # In case profile doesn't exist for some reason, the signal should have handled it
                # but we can create it here if needed or just pass
                pass

        response = self.get_response(request)
        return response
