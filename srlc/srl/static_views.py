from django.http import Http404
from django.shortcuts import redirect, render


def PrivacyPolicy(request):
    """Returns privacy policy for the website."""
    return render(request, "srl/privacy_policy.html")


def Changelog(request):
    """Returns the changelog for the website."""
    return redirect("https://github.com/ThePackle/SRLC/blob/main/CHANGELOG.md")


def FAQ(request):
    """Returns the FAQ section for the website."""
    return render(request, "srl/faq.html")


def page_not_found(request, exception=None):
    """Returns the user to the main page if 404'd."""
    if exception and isinstance(exception, Http404):
        return redirect("/")
    else:
        raise exception
