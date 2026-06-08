from fastapi import APIRouter, Request

from limiter import GEMINI_DAILY_LIMIT, GEMINI_RATE_LIMIT, limiter
from schemas import SuggestionResponse
from services.suggestion_service import get_market_suggestion

router = APIRouter(prefix="/cards", tags=["suggestions"])


@router.get("/suggest", response_model=SuggestionResponse)
@limiter.limit(GEMINI_DAILY_LIMIT)
@limiter.limit(GEMINI_RATE_LIMIT)
def market_suggestion(request: Request, q: str):
    return get_market_suggestion(q)
