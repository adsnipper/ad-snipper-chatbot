from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    whatsapp: str = Field(min_length=8, max_length=25)
    source_page: str = Field(default="")
    country: str = Field(default="Unknown")
    device: str = Field(default="Unknown")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned.replace(" ", "").isalpha():
            raise ValueError("Name must contain letters and spaces only.")
        return cleaned

    @field_validator("whatsapp")
    @classmethod
    def validate_whatsapp(cls, value: str) -> str:
        allowed = "+0123456789 -()"
        cleaned = value.strip()
        if any(char not in allowed for char in cleaned):
            raise ValueError("WhatsApp number contains invalid characters.")
        digits = "".join(char for char in cleaned if char.isdigit())
        if len(digits) < 8:
            raise ValueError("WhatsApp number must contain at least 8 digits.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("Email must be a valid email address.")
        return cleaned


class LeadRecord(BaseModel):
    conversation_id: str
    timestamp: datetime
    name: str
    email: str
    whatsapp: str
    source_page: str
    country: str
    device: str
    chat_started: Optional[datetime] = None
    chat_ended: Optional[datetime] = None
    message_count: int = 0
    intent_score: int = 0
    calendly_booked: bool = False
    meeting_date: Optional[str] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    conversation_id: str
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    should_offer_booking: bool
    intent_score: int
    calendly_url: Optional[str] = None
    show_calendly_embed: bool = False
    calendly_embed_url: Optional[str] = None


class SessionData(BaseModel):
    lead: LeadRecord
    messages: List[ChatMessage] = Field(default_factory=list)
    booking_offer_made: bool = False
    booking_declined: bool = False
    awaiting_booking_confirmation: bool = False
    calendly_embed_shown: bool = False


class CalendlyWebhookPayload(BaseModel):
    event: str = Field(default="")
    payload: dict = Field(default_factory=dict)