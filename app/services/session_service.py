import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from redis import Redis
from redis.exceptions import RedisError

from app.models import LeadRecord, SessionData


class SessionService:
    def __init__(self, redis_url: str, ttl_minutes: int) -> None:
        self.ttl_minutes = ttl_minutes
        self.redis: Optional[Redis] = None
        self.memory_store: dict[str, SessionData] = {}

        if redis_url:
            try:
                self.redis = Redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
            except RedisError:
                self.redis = None

    def _key(self, conversation_id: str) -> str:
        return f"session:{conversation_id}"

    def save(self, session: SessionData) -> None:
        if self.redis:
            self.redis.setex(
                self._key(session.lead.conversation_id),
                timedelta(minutes=self.ttl_minutes),
                session.model_dump_json(),
            )
            return
        self.memory_store[session.lead.conversation_id] = session

    def get(self, conversation_id: str) -> Optional[SessionData]:
        if self.redis:
            raw = self.redis.get(self._key(conversation_id))
            if not raw:
                return None
            return SessionData.model_validate_json(raw)
        return self.memory_store.get(conversation_id)

    def create(self, lead: LeadRecord) -> SessionData:
        session = SessionData(lead=lead)
        self.save(session)
        return session

    def mark_chat_started(self, conversation_id: str) -> Optional[SessionData]:
        session = self.get(conversation_id)
        if not session:
            return None
        if not session.lead.chat_started:
            session.lead.chat_started = datetime.now(timezone.utc)
            self.save(session)
        return session

    def mark_chat_ended(self, conversation_id: str) -> Optional[SessionData]:
        session = self.get(conversation_id)
        if not session:
            return None
        session.lead.chat_ended = datetime.now(timezone.utc)
        self.save(session)
        return session