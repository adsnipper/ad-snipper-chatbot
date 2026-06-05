from urllib.parse import urlencode

from app.config import Settings
from app.models import LeadRecord


class CalendlyService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def enabled(self) -> bool:
        return bool(self.settings.calendly_event_url)

    def build_embed_url(self, lead: LeadRecord) -> str | None:
        if not self.enabled:
            return None

        query = urlencode(
            {
                "hide_gdpr_banner": "1",
                "embed_domain": "adsnipper.com",
                "embed_type": "Inline",
                "name": lead.name,
                "email": lead.email,
            }
        )
        return f"{self.settings.calendly_event_url}?{query}"