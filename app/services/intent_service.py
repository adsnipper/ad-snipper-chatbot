INTENT_KEYWORDS = {
    "price": 3,
    "pricing": 3,
    "cost": 3,
    "quote": 4,
    "budget": 3,
    "hire": 3,
    "book": 4,
    "call": 3,
    "discovery": 4,
    "get started": 3,
    "available": 2,
    "availability": 2,
    "need help": 2,
    "looking for": 2,
    "specialist": 2,
}

BOOKING_ACCEPTANCE_KEYWORDS = {
    "yes",
    "yeah",
    "yep",
    "sure",
    "okay",
    "ok",
    "book it",
    "let's do it",
    "lets do it",
    "schedule it",
    "show me",
    "send it",
    "pull it up",
}

BOOKING_REJECTION_KEYWORDS = {
    "no",
    "no thanks",
    "not now",
    "not yet",
    "later",
    "maybe later",
    "i have more questions",
    "questions first",
}

DIRECT_BOOKING_KEYWORDS = {
    "book a call",
    "book the call",
    "book discovery",
    "schedule a call",
    "schedule discovery",
    "show calendar",
    "show me the calendar",
    "pull up calendar",
    "pull up the calendar",
    "how do i book",
    "want to book",
}


def score_intent(message: str, exchange_count: int) -> int:
    score = 0
    lowered = message.lower()
    for keyword, value in INTENT_KEYWORDS.items():
        if keyword in lowered:
            score += value
    if exchange_count >= 6:
        score += 2
    return min(score, 10)


def should_offer_booking(message: str, exchange_count: int) -> bool:
    return score_intent(message, exchange_count) >= 4


def is_booking_acceptance(message: str) -> bool:
    lowered = " ".join(message.lower().split())
    return any(keyword in lowered for keyword in BOOKING_ACCEPTANCE_KEYWORDS)


def is_booking_rejection(message: str) -> bool:
    lowered = " ".join(message.lower().split())
    return any(keyword in lowered for keyword in BOOKING_REJECTION_KEYWORDS)


def is_direct_booking_request(message: str) -> bool:
    lowered = " ".join(message.lower().split())
    return any(keyword in lowered for keyword in DIRECT_BOOKING_KEYWORDS)