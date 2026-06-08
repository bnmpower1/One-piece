from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import httpx

from schemas import PriceResponse
from services.card_service import get_card_price

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("/price", response_model=PriceResponse)
def card_price(q: str):
    return get_card_price(q)


@router.get("/image")
def proxy_image(url: str):
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=10)
        resp.raise_for_status()
    except Exception:
        raise HTTPException(status_code=404, detail="Image not found")
    content_type = resp.headers.get("content-type", "image/png")
    return Response(content=resp.content, media_type=content_type)
