import os
from functools import lru_cache
from typing import List

from pydantic import BaseModel

try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    pass


class Settings(BaseModel):
    app_name: str = "Ad Snipper Chatbot API"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    allowed_origins: str = "http://localhost:8000,http://127.0.0.1:8000"

    openai_api_key: str = ""
    openai_model: str = "gpt-5-mini"

    google_sheets_spreadsheet_id: str = ""
    google_sheets_credentials_json: str = ""
    google_sheets_credentials_file: str = ""
    google_sheets_leads_tab: str = "Leads"
    google_sheets_conversations_tab: str = "Conversations"

    calendly_event_url: str = ""
    calendly_webhook_signing_key: str = ""

    redis_url: str = ""
    session_ttl_minutes: int = 30

    temp_email_domains: str = "mailinator.com,tempmail.com,10minutemail.com,guerrillamail.com"
    max_messages_per_hour: int = 30

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def temp_email_domains_list(self) -> List[str]:
        return [domain.strip().lower() for domain in self.temp_email_domains.split(",") if domain.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Ad Snipper Chatbot API"),
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        allowed_origins=os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:8000,http://127.0.0.1:8000",
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5-mini"),
        google_sheets_spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
        google_sheets_credentials_json=os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON", ""),
        google_sheets_credentials_file=os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", ""),
        google_sheets_leads_tab=os.getenv("GOOGLE_SHEETS_LEADS_TAB", "Leads"),
        google_sheets_conversations_tab=os.getenv("GOOGLE_SHEETS_CONVERSATIONS_TAB", "Conversations"),
        calendly_event_url=os.getenv("CALENDLY_EVENT_URL", ""),
        calendly_webhook_signing_key=os.getenv("CALENDLY_WEBHOOK_SIGNING_KEY", ""),
        redis_url=os.getenv("REDIS_URL", ""),
        session_ttl_minutes=int(os.getenv("SESSION_TTL_MINUTES", "30")),
        temp_email_domains=os.getenv(
            "TEMP_EMAIL_DOMAINS",
            "mailinator.com,tempmail.com,10minutemail.com,guerrillamail.com",
        ),
        max_messages_per_hour=int(os.getenv("MAX_MESSAGES_PER_HOUR", "30")),
    )