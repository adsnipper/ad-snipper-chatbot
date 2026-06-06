# import re
# from dataclasses import dataclass

# from app.knowledge_base import COMPANY_KNOWLEDGE_BASE


# STOP_WORDS = {
#     "a",
#     "about",
#     "and",
#     "are",
#     "as",
#     "at",
#     "can",
#     "do",
#     "does",
#     "for",
#     "from",
#     "how",
#     "i",
#     "in",
#     "is",
#     "it",
#     "me",
#     "of",
#     "on",
#     "or",
#     "our",
#     "tell",
#     "that",
#     "the",
#     "this",
#     "to",
#     "what",
#     "with",
#     "you",
#     "your",
# }


# @dataclass(frozen=True)
# class KnowledgeChunk:
#     title: str
#     body: str
#     tokens: set[str]


# def _tokenize(text: str) -> set[str]:
#     words = re.findall(r"[a-z0-9+]+", text.lower())
#     return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


# def _build_chunks() -> list[KnowledgeChunk]:
#     chunks: list[KnowledgeChunk] = []
#     current_title = "Company overview"
#     current_lines: list[str] = []

#     for raw_line in COMPANY_KNOWLEDGE_BASE.strip().splitlines():
#         line = raw_line.strip()
#         if not line:
#             continue

#         if line.endswith(":") and not line.startswith("-"):
#             if current_lines:
#                 body = "\n".join(current_lines)
#                 chunks.append(KnowledgeChunk(current_title, body, _tokenize(f"{current_title} {body}")))
#             current_title = line[:-1]
#             current_lines = []
#             continue

#         current_lines.append(line)

#     if current_lines:
#         body = "\n".join(current_lines)
#         chunks.append(KnowledgeChunk(current_title, body, _tokenize(f"{current_title} {body}")))

#     return chunks


# KNOWLEDGE_CHUNKS = _build_chunks()


# class KnowledgeService:
#     def retrieve_context(self, question: str, max_chunks: int = 6) -> str:
#         query_tokens = _tokenize(question)
#         if not query_tokens:
#             return COMPANY_KNOWLEDGE_BASE

#         scored: list[tuple[int, KnowledgeChunk]] = []
#         for chunk in KNOWLEDGE_CHUNKS:
#             overlap = len(query_tokens.intersection(chunk.tokens))
#             if overlap:
#                 scored.append((overlap, chunk))

#         if not scored:
#             return COMPANY_KNOWLEDGE_BASE

#         scored.sort(key=lambda item: item[0], reverse=True)
#         selected = [chunk for _, chunk in scored[:max_chunks]]
#         sections = [f"{chunk.title}:\n{chunk.body}" for chunk in selected]
#         return "\n\n".join(sections)

#     def build_context_answer(self, question: str, context: str) -> str:
#         lowered = question.lower()
#         lines = [line.strip() for line in context.splitlines() if line.strip()]
#         content_lines = [line for line in lines if not line.endswith(":")]

#         if any(word in lowered for word in ("service", "provide", "offer")):
#             services = [
#                 line
#                 for line in content_lines
#                 if any(
#                     marker in line.lower()
#                     for marker in (
#                         "ads",
#                         "creative",
#                         "virtual",
#                         "sdr",
#                         "automation",
#                         "chatbot",
#                         "video",
#                         "design",
#                         "crm",
#                     )
#                 )
#                 and "$" not in line
#             ]
#             if services:
#                 return "We provide " + "; ".join(services[:8]) + "."

#         if any(word in lowered for word in ("cost", "price", "pricing", "monthly", "budget")):
#             pricing = [line for line in content_lines if "$" in line or "pricing" in line.lower()]
#             if pricing:
#                 return " ".join(pricing[:5])

#         if any(word in lowered for word in ("different", "agency", "marketing agency")):
#             differentiators = [
#                 line
#                 for line in content_lines
#                 if any(marker in line.lower() for marker in ("not a typical", "inside", "extension", "dedicated"))
#             ]
#             if differentiators:
#                 return " ".join(differentiators[:4])

#         if any(word in lowered for word in ("fit", "replace", "replacement")):
#             replacements = [line for line in content_lines if "replace" in line.lower() or "fit" in line.lower()]
#             if replacements:
#                 return " ".join(replacements[:3])

#         if any(word in lowered for word in ("nda", "contract", "agreement", "legal")):
#             legal = [
#                 line
#                 for line in content_lines
#                 if any(marker in line.lower() for marker in ("nda", "agreement", "contract", "notice", "lock"))
#             ]
#             if legal:
#                 return " ".join(legal[:4])

#         if any(word in lowered for word in ("start", "onboard", "onboarding", "process")):
#             process = [
#                 line
#                 for line in content_lines
#                 if any(marker in line.lower() for marker in ("step", "start", "within", "candidate", "discovery"))
#             ]
#             if process:
#                 return " ".join(process[:5])

#         if content_lines:
#             return " ".join(content_lines[:4])

#         return (
#             "We can help with Ad Snipper services, pricing, onboarding, staffing fit, and Discovery Call booking."
#         )


import re
from dataclasses import dataclass

from app.knowledge_base import COMPANY_KNOWLEDGE_BASE


STOP_WORDS = {
    "a",
    "about",
    "and",
    "are",
    "as",
    "at",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "of",
    "on",
    "or",
    "our",
    "tell",
    "that",
    "the",
    "this",
    "to",
    "what",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class KnowledgeChunk:
    title: str
    body: str
    tokens: set[str]


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9+]+", text.lower())
    return {word for word in words if len(word) > 2 and word not in STOP_WORDS}


def _build_chunks() -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    current_title = "Company overview"
    current_lines: list[str] = []

    for raw_line in COMPANY_KNOWLEDGE_BASE.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.endswith(":") and not line.startswith("-"):
            if current_lines:
                body = "\n".join(current_lines)
                chunks.append(
                    KnowledgeChunk(
                        current_title,
                        body,
                        _tokenize(f"{current_title} {body}"),
                    )
                )
            current_title = line[:-1]
            current_lines = []
            continue

        current_lines.append(line)

    if current_lines:
        body = "\n".join(current_lines)
        chunks.append(
            KnowledgeChunk(
                current_title,
                body,
                _tokenize(f"{current_title} {body}"),
            )
        )

    return chunks


KNOWLEDGE_CHUNKS = _build_chunks()


class KnowledgeService:
    def retrieve_context(self, question: str, max_chunks: int = 4) -> str:
        query_tokens = _tokenize(question)
        if not query_tokens:
            return COMPANY_KNOWLEDGE_BASE

        scored: list[tuple[int, KnowledgeChunk]] = []
        for chunk in KNOWLEDGE_CHUNKS:
            overlap = len(query_tokens.intersection(chunk.tokens))
            if overlap:
                scored.append((overlap, chunk))

        if not scored:
            return COMPANY_KNOWLEDGE_BASE

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = [chunk for _, chunk in scored[:max_chunks]]
        sections = [f"{chunk.title}:\n{chunk.body}" for chunk in selected]
        return "\n\n".join(sections)

    def build_context_answer(self, question: str, context: str) -> str:
        lowered = question.lower()
        lines = [line.strip() for line in context.splitlines() if line.strip()]
        content_lines = [line for line in lines if not line.endswith(":")]

        if "project" in lowered:
            return (
                "Yes. We offer project-based work after reviewing your brief and estimating the hours, "
                "timeline, and cost. It is billed 50% upfront and 50% on completion."
            )

        if any(word in lowered for word in ("fit", "replace", "replacement")):
            return (
                "If the specialist is not the right fit or leaves, we provide a replacement within the "
                "14-day replacement period at no extra cost."
            )

        if "white-label" in lowered or "white label" in lowered or "reseller" in lowered:
            return (
                "Yes. We support white-label and reseller partnerships and offer partners a 15% discount "
                "across packages."
            )

        if any(word in lowered for word in ("service", "provide", "offer")):
            return (
                "We provide dedicated AI Automation Specialists, Marketing Associates, Creative Associates, "
                "and Virtual Assistants through project-based, part-time, full-time, or custom engagements."
            )

        if any(word in lowered for word in ("cost", "price", "pricing", "monthly", "budget", "much")):
            role_markers = (
                ("automation", "AI Automation Specialist"),
                ("marketing", "Marketing Associate"),
                ("media buyer", "Marketing Associate"),
                ("creative", "Creative Associate"),
                ("designer", "Creative Associate"),
                ("video editor", "Creative Associate"),
                ("virtual assistant", "Virtual Assistant"),
                (" va ", "Virtual Assistant"),
            )
            padded_question = f" {lowered} "

            for marker, role_name in role_markers:
                if marker in padded_question:
                    matching = [
                        line
                        for line in content_lines
                        if line.startswith(f"{role_name}:")
                    ]
                    if matching:
                        return matching[0]

            pricing = [
                line
                for line in content_lines
                if "$" in line or "pricing" in line.lower()
            ]
            if pricing:
                return pricing[0]

        if "working hours" in lowered or "operating hours" in lowered or "timezone" in lowered:
            return (
                "Our default hours are 6 PM to 2 AM Pakistan time, aligned with 9 AM to 5 PM US Eastern time. "
                "We can also arrange timezone flexibility for other regions."
            )

        if any(word in lowered for word in ("different", "agency", "marketing agency")):
            differentiators = [
                line
                for line in content_lines
                if any(
                    marker in line.lower()
                    for marker in (
                        "not a typical",
                        "inside",
                        "extension",
                        "dedicated",
                    )
                )
            ]
            if differentiators:
                return " ".join(differentiators[:2])

        if any(word in lowered for word in ("nda", "contract", "agreement", "legal")):
            legal = [
                line
                for line in content_lines
                if any(
                    marker in line.lower()
                    for marker in (
                        "nda",
                        "agreement",
                        "contract",
                        "notice",
                        "lock",
                    )
                )
            ]
            if legal:
                return " ".join(legal[:2])

        if any(word in lowered for word in ("start", "onboard", "onboarding", "process")):
            process = [
                line
                for line in content_lines
                if any(
                    marker in line.lower()
                    for marker in (
                        "step",
                        "start",
                        "within",
                        "candidate",
                        "discovery",
                    )
                )
            ]
            if process:
                return " ".join(process[:3])

        query_tokens = _tokenize(question)
        ranked_lines = sorted(
            content_lines,
            key=lambda line: len(query_tokens.intersection(_tokenize(line))),
            reverse=True,
        )
        relevant_lines = [
            line
            for line in ranked_lines
            if query_tokens.intersection(_tokenize(line))
        ]

        if relevant_lines:
            return " ".join(relevant_lines[:2])

        return (
            "We can help with Ad Snipper services, pricing, onboarding, "
            "staffing fit, and Discovery Call booking."
        )