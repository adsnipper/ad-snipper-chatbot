# import re
# from typing import Any, Iterable

# from openai import APIError, OpenAI, RateLimitError

# from app.config import Settings
# from app.models import ChatMessage
# from app.prompts import build_system_prompt


# class OpenAIService:
#     def __init__(self, settings: Settings) -> None:
#         self.settings = settings
#         self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

#     def build_input(self, messages: Iterable[ChatMessage], company_context: str) -> list[dict]:
#         output = [
#             {
#                 "role": "system",
#                 "content": (
#                     "Use this company knowledge as your source of truth for this turn.\n\n"
#                     f"{company_context}"
#                 ),
#             }
#         ]
#         for message in messages:
#             output.append({"role": message.role, "content": message.content})
#         return output

#     def _extract_text(self, response: Any) -> str:
#         text = getattr(response, "output_text", "") or ""
#         if text:
#             return text.strip()

#         if hasattr(response, "model_dump"):
#             dumped = response.model_dump()
#             text = self._recursive_find_text(dumped)
#             if text:
#                 return text.strip()

#         output = getattr(response, "output", []) or []
#         for item in output:
#             content_items = getattr(item, "content", None)
#             if content_items is None and isinstance(item, dict):
#                 content_items = item.get("content", [])

#             for content in content_items or []:
#                 candidate = getattr(content, "text", None)
#                 if candidate:
#                     return candidate.strip()
#                 if isinstance(content, dict):
#                     candidate = content.get("text")
#                     if candidate:
#                         return str(candidate).strip()

#         return ""

#     def _recursive_find_text(self, value: Any) -> str:
#         if isinstance(value, dict):
#             if isinstance(value.get("text"), str) and value["text"].strip():
#                 return value["text"]
#             if isinstance(value.get("content"), str) and value["content"].strip():
#                 return value["content"]
#             for child in value.values():
#                 found = self._recursive_find_text(child)
#                 if found:
#                     return found

#         if isinstance(value, list):
#             for child in value:
#                 found = self._recursive_find_text(child)
#                 if found:
#                     return found

#         return ""

#     def _request_response(self, messages: Iterable[ChatMessage], company_context: str) -> str:
#         response = self.client.responses.create(
#             model=self.settings.openai_model,
#             instructions=build_system_prompt(),
#             input=self.build_input(messages, company_context),
#             max_output_tokens=800,
#         )
#         return self._extract_text(response)

#     def _sanitize_reply(self, reply: str) -> str:
#         cleaned = (
#             reply.replace("—", ", ")
#             .replace("–", "-")
#             .replace("â€”", ", ")
#             .replace("â€“", "-")
#         )
#         patterns = (
#             r"\s*Sounds like a Discovery Call would be the fastest way.*?(?:slot|calendar|chat)\??",
#             r"\s*Want (?:me|us) to .*?(?:slot|calendar|call).*?\?",
#             r"\s*Want to book .*?Discovery Call.*?\?",
#             r"\s*Would you like (?:me|us) to .*?(?:slot|calendar|call).*?\?",
#         )
#         for pattern in patterns:
#             cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE | re.DOTALL)
#         cleaned = re.sub(r"[ \t]+-[ \t]+", ", ", cleaned)
#         cleaned = re.sub(r"(?m)^\s*-\s+", "", cleaned)
#         cleaned = re.sub(r"\s+,", ",", cleaned)
#         cleaned = re.sub(r",[ \t]{2,}", ", ", cleaned)
#         cleaned = re.sub(r",\s*,+", ",", cleaned)
#         cleaned = re.sub(r",\s*\.", ".", cleaned)
#         return re.sub(r"\n{3,}", "\n\n", cleaned).strip()

#     def get_response(self, messages: Iterable[ChatMessage], company_context: str, fallback_reply: str) -> str:
#         if not self.client:
#             return fallback_reply

#         try:
#             text = self._request_response(messages, company_context)
#             if text:
#                 return self._sanitize_reply(text)
#         except RateLimitError:
#             return fallback_reply
#         except APIError:
#             return fallback_reply
#         return self._sanitize_reply(fallback_reply)

#     @staticmethod
#     def is_generic_fallback(reply: str) -> bool:
#         lowered = " ".join(reply.lower().split())
#         generic_markers = (
#             "we have the details on our services",
#             "tell us what role or outcome you need",
#             "our live ai replies are temporarily unavailable",
#         )
#         return any(marker in lowered for marker in generic_markers)




import re
from typing import Any, Iterable

from openai import APIError, OpenAI, RateLimitError

from app.config import Settings
from app.models import ChatMessage
from app.prompts import build_system_prompt


class OpenAIService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = (
            OpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key
            else None
        )

    def build_input(
        self,
        messages: Iterable[ChatMessage],
        company_context: str,
    ) -> list[dict]:
        output = [
            {
                "role": "system",
                "content": (
                    "Use this company knowledge as your source of truth for this turn.\n\n"
                    f"{company_context}"
                ),
            }
        ]

        for message in messages:
            output.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )

        return output

    def _extract_text(self, response: Any) -> str:
        text = getattr(response, "output_text", "") or ""
        if text:
            return text.strip()

        if hasattr(response, "model_dump"):
            dumped = response.model_dump()
            text = self._recursive_find_text(dumped)

            if text:
                return text.strip()

        output = getattr(response, "output", []) or []

        for item in output:
            content_items = getattr(item, "content", None)

            if content_items is None and isinstance(item, dict):
                content_items = item.get("content", [])

            for content in content_items or []:
                candidate = getattr(content, "text", None)

                if candidate:
                    return candidate.strip()

                if isinstance(content, dict):
                    candidate = content.get("text")

                    if candidate:
                        return str(candidate).strip()

        return ""

    def _recursive_find_text(self, value: Any) -> str:
        if isinstance(value, dict):
            if isinstance(value.get("text"), str) and value["text"].strip():
                return value["text"]

            if isinstance(value.get("content"), str) and value["content"].strip():
                return value["content"]

            for child in value.values():
                found = self._recursive_find_text(child)

                if found:
                    return found

        if isinstance(value, list):
            for child in value:
                found = self._recursive_find_text(child)

                if found:
                    return found

        return ""

    def _request_response(
        self,
        messages: Iterable[ChatMessage],
        company_context: str,
    ) -> str:
        response = self.client.responses.create(
            model=self.settings.openai_model,
            instructions=build_system_prompt(),
            input=self.build_input(messages, company_context),
            max_output_tokens=350,
        )

        return self._extract_text(response)

    def _sanitize_reply(self, reply: str) -> str:
        cleaned = (
            reply.replace("â€”", ", ")
            .replace("â€“", "-")
            .replace("Ã¢â‚¬â€", ", ")
            .replace("Ã¢â‚¬â€œ", "-")
        )

        patterns = (
            r"\s*Sounds like a Discovery Call would be the fastest way.*?(?:slot|calendar|chat)\??",
            r"\s*Want (?:me|us) to .*?(?:slot|calendar|call).*?\?",
            r"\s*Want to book .*?Discovery Call.*?\?",
            r"\s*Would you like (?:me|us) to .*?(?:slot|calendar|call).*?\?",
        )

        for pattern in patterns:
            cleaned = re.sub(
                pattern,
                "",
                cleaned,
                flags=re.IGNORECASE | re.DOTALL,
            )

        cleaned = re.sub(r"[ \t]+-[ \t]+", ", ", cleaned)
        cleaned = re.sub(r"(?m)^\s*-\s+", "", cleaned)
        cleaned = re.sub(r"\s+,", ",", cleaned)
        cleaned = re.sub(r",[ \t]{2,}", ", ", cleaned)
        cleaned = re.sub(r",\s*,+", ",", cleaned)
        cleaned = re.sub(r",\s*\.", ".", cleaned)

        return re.sub(r"\n{3,}", "\n\n", cleaned).strip()

    def get_response(
        self,
        messages: Iterable[ChatMessage],
        company_context: str,
        fallback_reply: str,
    ) -> str:
        if not self.client:
            return fallback_reply

        try:
            text = self._request_response(messages, company_context)

            if text:
                return self._sanitize_reply(text)

        except RateLimitError:
            return fallback_reply
        except APIError:
            return fallback_reply

        return self._sanitize_reply(fallback_reply)

    @staticmethod
    def is_generic_fallback(reply: str) -> bool:
        lowered = " ".join(reply.lower().split())

        generic_markers = (
            "we have the details on our services",
            "tell us what role or outcome you need",
            "our live ai replies are temporarily unavailable",
        )

        return any(marker in lowered for marker in generic_markers)