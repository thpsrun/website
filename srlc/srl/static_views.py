from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render


def PrivacyPolicy(
    request: HttpRequest,
) -> HttpResponse:
    """Returns privacy policy for the website."""
    return render(request, "srl/privacy_policy.html")


def TourneyView(
    request: HttpRequest,
) -> HttpResponse:
    """Returns tournament information."""
    return render(request, "srl/tourney.html")


def Changelog(
    request: HttpRequest,
) -> HttpResponse:
    """Returns the changelog for the website."""
    return redirect("https://github.com/thpsrun/website/blob/main/CHANGELOG.md")


def FAQ(
    request: HttpRequest,
) -> HttpResponse:
    """Returns the FAQ section for the website."""
    return render(request, "srl/faq.html")


def page_not_found(
    request: HttpRequest,
    exception: str,
) -> HttpResponse:
    """Returns the user to the main page if 404'd."""
    if exception and isinstance(exception, Http404):
        return redirect("/")
    else:
        raise exception
