from django.shortcuts import redirect,render
from django.http import Http404

def PrivacyPolicy(request):
    return render(request, "srl/privacy_policy.html")

def Changelog(request):
    return render(request, "srl/changelog.html")

def FAQ(request):
    return render(request, "srl/faq.html")

def page_not_found(request, exception=None):
    if exception and isinstance(exception, Http404):
        return redirect("/")
    else:
        raise exception
