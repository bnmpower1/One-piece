from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from database import get_db
from limiter import GEMINI_RATE_LIMIT, limiter
from schemas import SuggestionResponse
from services.suggestion_service import get_market_suggestion

router = APIRouter(prefix="/cards", tags=["suggestions"])


@router.get("/suggest", response_model=SuggestionResponse)
@limiter.limit(GEMINI_RATE_LIMIT)
def market_suggestion(request: Request, q: str, db: Session = Depends(get_db)):
    return get_market_suggestion(db, q)
