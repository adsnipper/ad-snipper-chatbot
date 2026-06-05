# from datetime import datetime, timezone
# from pathlib import Path
# from uuid import uuid4

# from fastapi import FastAPI, HTTPException, Request
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import FileResponse
# from fastapi.staticfiles import StaticFiles
# from slowapi import Limiter, _rate_limit_exceeded_handler
# from slowapi.errors import RateLimitExceeded
# from slowapi.util import get_remote_address

# from app.config import get_settings
# from app.models import CalendlyWebhookPayload, ChatMessage, ChatRequest, ChatResponse, LeadCreate, LeadRecord
# from app.services.calendly_service import CalendlyService
# from app.services.intent_service import (
#     is_booking_acceptance,
#     is_booking_rejection,
#     is_direct_booking_request,
#     score_intent,
#     should_offer_booking,
# )
# from app.services.knowledge_service import KnowledgeService
# from app.services.openai_service import OpenAIService
# from app.services.session_service import SessionService
# from app.services.sheets_service import SheetsService

# settings = get_settings()
# limiter = Limiter(key_func=get_remote_address)

# app = FastAPI(title=settings.app_name)
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.allowed_origins_list,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# static_dir = Path(__file__).resolve().parent.parent / "static"
# app.mount("/static", StaticFiles(directory=static_dir), name="static")

# session_service = SessionService(settings.redis_url, settings.session_ttl_minutes)
# sheets_service = SheetsService(settings)
# openai_service = OpenAIService(settings)
# calendly_service = CalendlyService(settings)
# knowledge_service = KnowledgeService()


# @app.get("/")
# async def root() -> FileResponse:
#     return FileResponse(static_dir / "index.html")


# @app.get("/api/health")
# async def health() -> dict:
#     return {
#         "status": "ok",
#         "app": settings.app_name,
#         "sheets_enabled": sheets_service.enabled,
#         "redis_enabled": session_service.redis is not None,
#         "openai_configured": bool(settings.openai_api_key),
#         "calendly_enabled": calendly_service.enabled,
#     }


# @app.post("/api/lead")
# @limiter.limit("10/minute")
# async def create_lead(request: Request, payload: LeadCreate) -> dict:
#     email_domain = payload.email.split("@")[-1].lower()
#     if email_domain in settings.temp_email_domains_list:
#         raise HTTPException(status_code=400, detail="Disposable email addresses are not allowed.")

#     conversation_id = str(uuid4())
#     lead = LeadRecord(
#         conversation_id=conversation_id,
#         timestamp=datetime.now(timezone.utc),
#         name=payload.name,
#         email=payload.email,
#         whatsapp=payload.whatsapp,
#         source_page=payload.source_page,
#         country=payload.country,
#         device=payload.device,
#     )
#     session_service.create(lead)
#     sheets_service.append_lead(lead)
#     return {"conversation_id": conversation_id, "first_name": payload.name.split()[0]}


# @app.get("/api/session/{conversation_id}")
# async def get_session(conversation_id: str) -> dict:
#     session = session_service.get(conversation_id)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found.")
#     return session.model_dump()


# @app.post("/api/session/{conversation_id}/close")
# async def close_session(conversation_id: str) -> dict:
#     session = session_service.mark_chat_ended(conversation_id)
#     if not session:
#         raise HTTPException(status_code=404, detail="Session not found.")
#     sheets_service.append_lead(session.lead)
#     return {"closed": True}


# @app.post("/api/chat", response_model=ChatResponse)
# @limiter.limit("30/hour")
# async def chat(request: Request, payload: ChatRequest) -> ChatResponse:
#     session = session_service.get(payload.conversation_id)
#     if not session:
#         raise HTTPException(status_code=404, detail="Conversation not found.")

#     started_session = session_service.mark_chat_started(payload.conversation_id)
#     if started_session:
#         session = started_session

#     user_message = ChatMessage(role="user", content=payload.message)
#     session.messages.append(user_message)
#     sheets_service.append_conversation_message(session.lead.conversation_id, session.lead.email, user_message)

#     exchange_count = len([message for message in session.messages if message.role == "user"])
#     intent_score = score_intent(payload.message, exchange_count)
#     accepting_booking = session.awaiting_booking_confirmation and is_booking_acceptance(payload.message)
#     declining_booking = session.awaiting_booking_confirmation and is_booking_rejection(payload.message)
#     direct_booking_request = is_direct_booking_request(payload.message)
#     can_offer_booking = (
#         settings.calendly_event_url
#         and not session.booking_offer_made
#         and not session.booking_declined
#         and not session.calendly_embed_shown
#     )
#     offer_booking = can_offer_booking and (
#         should_offer_booking(payload.message, exchange_count) or exchange_count >= 6
#     )
#     booking_offer_created = False

#     show_calendly_embed = False
#     calendly_embed_url = None

#     if (accepting_booking or direct_booking_request) and calendly_service.enabled:
#         session.awaiting_booking_confirmation = False
#         session.booking_declined = False
#         session.booking_offer_made = True
#         session.calendly_embed_shown = True
#         show_calendly_embed = True
#         calendly_embed_url = calendly_service.build_embed_url(session.lead)
#         reply = (
#             "Perfect. I've opened our 30-minute Discovery Call scheduler below. "
#             "Pick the time that works best for you and Calendly will send the confirmation right away."
#         )
#     elif declining_booking:
#         session.awaiting_booking_confirmation = False
#         session.booking_declined = True
#         reply = "No problem. We can keep answering your questions here, and you can ask for the calendar whenever you are ready."
#     else:
#         company_context = knowledge_service.retrieve_context(payload.message)
#         fallback_reply = knowledge_service.build_context_answer(payload.message, company_context)
#         reply = openai_service.get_response(session.messages[-12:], company_context, fallback_reply)

#         if offer_booking:
#             session.booking_offer_made = True
#             session.awaiting_booking_confirmation = True
#             booking_offer_created = True
#             reply = (
#                 f"{reply}\n\n"
#                 "Sounds like a Discovery Call would be the fastest way to map this out for you. "
#                 "Want me to pull up our 30-minute calendar inside the chat?"
#             )

#     assistant_message = ChatMessage(role="assistant", content=reply)
#     session.messages.append(assistant_message)
#     sheets_service.append_conversation_message(session.lead.conversation_id, session.lead.email, assistant_message)

#     session.lead.intent_score = max(session.lead.intent_score, intent_score)
#     session.lead.message_count = len([message for message in session.messages if message.role in {"user", "assistant"}])
#     session_service.save(session)
#     sheets_service.append_lead(session.lead)

#     return ChatResponse(
#         conversation_id=session.lead.conversation_id,
#         reply=reply,
#         should_offer_booking=booking_offer_created,
#         intent_score=intent_score,
#         calendly_url=settings.calendly_event_url if session.booking_offer_made else None,
#         show_calendly_embed=show_calendly_embed,
#         calendly_embed_url=calendly_embed_url,
#     )


# @app.post("/api/calendly-webhook")
# async def calendly_webhook(payload: CalendlyWebhookPayload) -> dict:
#     body = payload.payload or {}
#     invitee = body.get("invitee", {}) if isinstance(body, dict) else {}
#     tracking = body.get("tracking", {}) if isinstance(body, dict) else {}
#     conversation_id = tracking.get("conversation_id") or invitee.get("conversation_id") or ""
#     meeting_date = invitee.get("start_time", "")

#     if conversation_id:
#         session = session_service.get(conversation_id)
#         if session:
#             session.lead.calendly_booked = payload.event in {"invitee.created", "booking.created"}
#             session.lead.meeting_date = meeting_date
#             session_service.save(session)
#         sheets_service.update_booking_status(
#             conversation_id=conversation_id,
#             booked=payload.event in {"invitee.created", "booking.created"},
#             meeting_date=meeting_date,
#         )

#     return {"received": True}






import hashlib
import hmac
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.models import CalendlyWebhookPayload, ChatMessage, ChatRequest, ChatResponse, LeadCreate, LeadRecord
from app.services.calendly_service import CalendlyService
from app.services.intent_service import (
    is_booking_acceptance,
    is_booking_rejection,
    is_direct_booking_request,
    score_intent,
    should_offer_booking,
)
from app.services.knowledge_service import KnowledgeService
from app.services.openai_service import OpenAIService
from app.services.session_service import SessionService
from app.services.sheets_service import SheetsService

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title=settings.app_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

session_service = SessionService(settings.redis_url, settings.session_ttl_minutes)
sheets_service = SheetsService(settings)
openai_service = OpenAIService(settings)
calendly_service = CalendlyService(settings)
knowledge_service = KnowledgeService()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/health")
async def health() -> dict:
    response = {
        "status": "ok",
        "app": settings.app_name,
    }
    if settings.app_env != "production":
        response.update(
            {
                "sheets_enabled": sheets_service.enabled,
                "redis_enabled": session_service.redis is not None,
                "openai_configured": bool(settings.openai_api_key),
                "calendly_enabled": calendly_service.enabled,
            }
        )
    return response


@app.post("/api/lead")
@limiter.limit("10/minute")
async def create_lead(request: Request, payload: LeadCreate) -> dict:
    email_domain = payload.email.split("@")[-1].lower()
    if email_domain in settings.temp_email_domains_list:
        raise HTTPException(status_code=400, detail="Disposable email addresses are not allowed.")

    conversation_id = str(uuid4())
    lead = LeadRecord(
        conversation_id=conversation_id,
        timestamp=datetime.now(timezone.utc),
        name=payload.name,
        email=payload.email,
        whatsapp=payload.whatsapp,
        source_page=payload.source_page,
        country=payload.country,
        device=payload.device,
    )
    session_service.create(lead)
    sheets_service.append_lead(lead)
    return {"conversation_id": conversation_id, "first_name": payload.name.split()[0]}


@app.get("/api/session/{conversation_id}")
async def get_session(conversation_id: str) -> dict:
    session = session_service.get(conversation_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return session.model_dump()


@app.post("/api/session/{conversation_id}/close")
async def close_session(conversation_id: str) -> dict:
    session = session_service.mark_chat_ended(conversation_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    sheets_service.append_lead(session.lead)
    return {"closed": True}


@app.post("/api/chat", response_model=ChatResponse)
@limiter.limit("30/hour")
async def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    session = session_service.get(payload.conversation_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    started_session = session_service.mark_chat_started(payload.conversation_id)
    if started_session:
        session = started_session

    user_message = ChatMessage(role="user", content=payload.message)
    session.messages.append(user_message)
    sheets_service.append_conversation_message(session.lead.conversation_id, session.lead.email, user_message)

    exchange_count = len([message for message in session.messages if message.role == "user"])
    intent_score = score_intent(payload.message, exchange_count)
    accepting_booking = session.awaiting_booking_confirmation and is_booking_acceptance(payload.message)
    declining_booking = session.awaiting_booking_confirmation and is_booking_rejection(payload.message)
    direct_booking_request = is_direct_booking_request(payload.message)
    can_offer_booking = (
        settings.calendly_event_url
        and not session.booking_offer_made
        and not session.booking_declined
        and not session.calendly_embed_shown
    )
    offer_booking = can_offer_booking and (
        should_offer_booking(payload.message, exchange_count) or exchange_count >= 6
    )
    booking_offer_created = False

    show_calendly_embed = False
    calendly_embed_url = None

    if (accepting_booking or direct_booking_request) and calendly_service.enabled:
        session.awaiting_booking_confirmation = False
        session.booking_declined = False
        session.booking_offer_made = True
        session.calendly_embed_shown = True
        show_calendly_embed = True
        calendly_embed_url = calendly_service.build_embed_url(session.lead)
        reply = (
            "Perfect. I've opened our 30-minute Discovery Call scheduler below. "
            "Pick the time that works best for you and Calendly will send the confirmation right away."
        )
    elif declining_booking:
        session.awaiting_booking_confirmation = False
        session.booking_declined = True
        reply = "No problem. We can keep answering your questions here, and you can ask for the calendar whenever you are ready."
    else:
        company_context = knowledge_service.retrieve_context(payload.message)
        fallback_reply = knowledge_service.build_context_answer(payload.message, company_context)
        reply = openai_service.get_response(session.messages[-12:], company_context, fallback_reply)
        if offer_booking:
            session.booking_offer_made = True
            session.awaiting_booking_confirmation = True
            booking_offer_created = True
            reply = (
                f"{reply}\n\n"
                "Sounds like a Discovery Call would be the fastest way to map this out for you. "
                "Want me to pull up our 30-minute calendar inside the chat?"
            )

    assistant_message = ChatMessage(role="assistant", content=reply)
    session.messages.append(assistant_message)
    sheets_service.append_conversation_message(session.lead.conversation_id, session.lead.email, assistant_message)

    session.lead.intent_score = max(session.lead.intent_score, intent_score)
    session.lead.message_count = len([message for message in session.messages if message.role in {"user", "assistant"}])
    session_service.save(session)
    sheets_service.append_lead(session.lead)

    return ChatResponse(
        conversation_id=session.lead.conversation_id,
        reply=reply,
        should_offer_booking=booking_offer_created,
        intent_score=intent_score,
        calendly_url=settings.calendly_event_url if session.booking_offer_made else None,
        show_calendly_embed=show_calendly_embed,
        calendly_embed_url=calendly_embed_url,
    )


def verify_calendly_signature(request_body: bytes, signature: str | None) -> None:
    if not settings.calendly_webhook_signing_key:
        return
    if not signature:
        raise HTTPException(status_code=401, detail="Missing Calendly webhook signature.")

    expected = hmac.new(
        settings.calendly_webhook_signing_key.encode("utf-8"),
        request_body,
        hashlib.sha256,
    ).hexdigest()
    normalized_signature = signature.replace("sha256=", "").strip()
    if not hmac.compare_digest(expected, normalized_signature):
        raise HTTPException(status_code=401, detail="Invalid Calendly webhook signature.")


@app.post("/api/calendly-webhook")
async def calendly_webhook(request: Request, payload: CalendlyWebhookPayload) -> dict:
    body_bytes = await request.body()
    verify_calendly_signature(
        body_bytes,
        request.headers.get("Calendly-Webhook-Signature")
        or request.headers.get("X-Calendly-Signature")
        or request.headers.get("Calendly-Signature"),
    )

    body = payload.payload or {}
    invitee = body.get("invitee", {}) if isinstance(body, dict) else {}
    tracking = body.get("tracking", {}) if isinstance(body, dict) else {}
    conversation_id = tracking.get("conversation_id") or invitee.get("conversation_id") or ""
    meeting_date = invitee.get("start_time", "")

    if conversation_id:
        session = session_service.get(conversation_id)
        if session:
            session.lead.calendly_booked = payload.event in {"invitee.created", "booking.created"}
            session.lead.meeting_date = meeting_date
            session_service.save(session)
        sheets_service.update_booking_status(
            conversation_id=conversation_id,
            booked=payload.event in {"invitee.created", "booking.created"},
            meeting_date=meeting_date,
        )

    return {"received": True}