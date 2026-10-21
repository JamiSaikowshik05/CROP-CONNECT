"""Extra template variables available on every page."""
from django.conf import settings

# Languages offered in the navigation bar, in the order shown to visitors.
NAV_LANGUAGE_CODES = ['te', 'en', 'hi', 'ta']


def nav_languages(request):
    names = dict(settings.LANGUAGES)
    return {'NAV_LANGUAGES': [(code, names[code]) for code in NAV_LANGUAGE_CODES if code in names]}
