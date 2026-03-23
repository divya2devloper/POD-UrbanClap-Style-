from django.shortcuts import render

def photographer_join(request):
    """
    Landing page for photographers to join the platform.
    """
    return render(request, "accounts/photographer_join.html")


def login_view(request):
    """
    Customer portal login page.
    """
    return render(request, "accounts/login.html")
