from .models import StoreSettings


def store_settings(request):
    """Makes `store_settings` available in every template (navbar, footer, contact page)."""
    return {"store_settings": StoreSettings.load()}
