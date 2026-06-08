from fastapi import APIRouter

from schemas import PriceResponse
from services.card_service import get_card_price

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/price", response_model=PriceResponse)
def card_price(q: str):
    return get_card_price(q)
