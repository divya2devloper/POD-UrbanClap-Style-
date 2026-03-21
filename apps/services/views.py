from django.shortcuts import render
from .models import ServiceCategory, SERVICE_PACKAGES


def service_list(request):
    categories = ServiceCategory.objects.all()
    return render(request, 'services/service_list.html', {
        'categories': categories,
        'service_packages': SERVICE_PACKAGES,
    })
