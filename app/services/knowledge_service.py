import re

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


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9+]+", text.lower())
    return {
        word
        for word in words
        if len(word) > 2 and word not in STOP_WORDS
    }


class KnowledgeService:
    def retrieve_context(self, question: str) -> str:
        # OpenAI receives the complete approved public knowledge base so it can
        # reason dynamically about differently worded and unexpected questions.
        return COMPANY_KNOWLEDGE_BASE

    def build_context_answer(self, question: str, context: str) -> str:
        """
        Builds a concise emergency fallback answer.

        Normal chatbot questions are answered dynamically by OpenAI. These
        answers are only used if OpenAI is unavailable or produces an
        incomplete response.
        """
        lowered = " ".join(question.lower().split())
        lines = [
            line.strip()
            for line in context.splitlines()
            if line.strip()
        ]
        content_lines = [
            line
            for line in lines
            if not line.endswith(":")
        ]

        if "what is ad snipper" in lowered or "tell me about ad snipper" in lowered:
            return (
                "Ad Snipper is a talent outsourcing and staff augmentation "
                "company that places dedicated specialists with clients."
            )

        if any(
            phrase in lowered
            for phrase in (
                "where are you based",
                "your location",
                "headquarters",
            )
        ):
            return (
                "We are headquartered in Karachi, Pakistan, and we also have "
                "a US-registered entity."
            )

        if any(
            phrase in lowered
            for phrase in (
                "how big is your team",
                "team size",
                "how many people",
            )
        ):
            return "We have 35+ in-house specialists."

        if "media buyer" in lowered and any(
            word in lowered
            for word in (
                "cost",
                "price",
                "pricing",
                "monthly",
                "budget",
                "much",
                "rate",
            )
        ):
            return (
                "Media buyers cost $10 per hour, $800 per month part-time, "
                "or $1,600 per month full-time."
            )

        if "media buyer" in lowered or "paid ads" in lowered:
            return (
                "Yes. Our media buyers manage Meta, Google, YouTube, TikTok, "
                "LinkedIn, Pinterest, and programmatic advertising."
            )

        if "video editor" in lowered and any(
            word in lowered
            for word in ("hire", "just", "only", "provide", "offer")
        ):
            return (
                "Yes. You can hire a dedicated Creative Associate specifically "
                "for video editing."
            )

        if "voice receptionist" in lowered or "voice agent" in lowered:
            return (
                "Yes. Our AI Automation Specialists build AI receptionists "
                "and voice agents using tools such as Retell, ElevenLabs, and Twilio."
            )

        if "what should i prepare" in lowered or "prepare for the call" in lowered:
            return (
                "Prepare a short overview of what you need, your current setup "
                "and challenges, preferred engagement type, timezone, and "
                "communication preference."
            )

        if (
            "who will i be speaking with" in lowered
            or "who will i speak with" in lowered
        ):
            return (
                "You will normally speak with a co-founder or another "
                "appropriate member of our team, depending on availability."
            )

        if "project" in lowered:
            return (
                "Yes. We offer project-based work after reviewing your brief "
                "and estimating the hours, timeline, and cost. It is billed "
                "50% upfront and 50% on completion."
            )

        if any(
            word in lowered
            for word in ("fit", "replace", "replacement")
        ):
            return (
                "If the specialist is not the right fit or leaves, we provide "
                "a replacement within the 14-day replacement period at no extra cost."
            )

        if (
            "white-label" in lowered
            or "white label" in lowered
            or "reseller" in lowered
        ):
            return (
                "Yes. We support white-label and reseller partnerships and "
                "offer partners a 15% discount across packages."
            )

        if "multiple placements" in lowered or "volume discount" in lowered:
            return (
                "Our confirmed standard discount is 15% for white-label and "
                "reseller partners. Discounts for multiple direct placements "
                "need confirmation from our team."
            )

        if "setup fee" in lowered or "recruitment fee" in lowered:
            return (
                "No. We do not charge setup, recruitment, or replacement fees."
            )

        if any(
            phrase in lowered
            for phrase in (
                "per hour or per month",
                "hourly or monthly",
                "payment options",
            )
        ):
            return (
                "We offer hourly, part-time monthly, full-time monthly, and "
                "project-based engagements."
            )

        if any(
            word in lowered
            for word in ("cost", "price", "pricing", "monthly", "budget", "much", "rate")
        ):
            role_markers = (
                ("automation", "AI Automation Specialist"),
                ("marketing", "Marketing Associate"),
                ("creative", "Creative Associate"),
                ("designer", "Creative Associate"),
                ("video editor", "Video Editor"),
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

        if "working hours" in lowered or "operating hours" in lowered or "timezone" in lowered:
            return (
                "Our default hours are 6 PM to 2 AM Pakistan time, aligned "
                "with 9 AM to 5 PM US Eastern time. We can also arrange "
                "timezone flexibility for other regions."
            )

        if any(
            phrase in lowered
            for phrase in (
                "different from a marketing agency",
                "different from an agency",
            )
        ):
            return (
                "Unlike a traditional agency, we place one dedicated specialist "
                "who works directly with your team while we handle hiring, "
                "training, and ongoing support."
            )

        if any(
            word in lowered
            for word in ("nda", "contract", "agreement", "legal")
        ):
            return (
                "We sign NDAs and service agreements before work begins. "
                "Staff-augmentation contracts are month-to-month with no "
                "long-term commitment."
            )

        if "how fast" in lowered or "start" in lowered:
            return (
                "We normally present 2 to 3 candidates within about 48 hours, "
                "and the selected specialist typically starts within 5 to 7 "
                "business days after contract signing."
            )

        if any(
            word in lowered
            for word in ("onboard", "onboarding", "process")
        ):
            return (
                "We identify your needs, present suitable candidates, let you "
                "interview and choose one, then complete the contract and onboarding."
            )

        if "manage" in lowered and any(
            word in lowered
            for word in ("directly", "you", "them")
        ):
            return (
                "You manage the specialist day to day, while we handle hiring, "
                "training, employment, timekeeping, support, feedback, and replacements."
            )

        if "case stud" in lowered or "portfolio" in lowered:
            return (
                "Yes. We can share relevant case studies and portfolios during "
                "the sales process or Discovery Call."
            )

        if any(word in lowered for word in ("service", "services")):
            return (
                "We provide dedicated AI Automation Specialists, Marketing "
                "Associates, Creative Associates, and Virtual Assistants through "
                "project-based, part-time, full-time, or custom engagements."
            )

        query_tokens = _tokenize(question)
        ranked_lines = sorted(
            content_lines,
            key=lambda line: len(
                query_tokens.intersection(_tokenize(line))
            ),
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
            "I do not have that detail confirmed yet, but our team can clarify it."
        )