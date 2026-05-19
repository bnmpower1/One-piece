from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import PriceResponse
from services.card_service import get_card_price

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/price", response_model=PriceResponse)
def card_price(q: str, db: Session = Depends(get_db)):
    return get_card_price(db, q)
