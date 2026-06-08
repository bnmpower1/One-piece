from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import httpx

from schemas import PriceResponse
from services.card_service import get_card_price

router = APIRouter(prefix="/cards", tags=["cards"])

_ALLOWED_IMAGE_HOSTS = {
    "en.onepiece-cardgame.com",
    "product-images.tcgplayer.com",
    "tcgplayer.com",
}


@router.get("/price", response_model=PriceResponse)
def card_price(q: str):
    return get_card_price(q)


@router.get("/image")
def proxy_image(url: str):
    host = urlparse(url).hostname or ""
    if not any(host == allowed or host.endswith("." + allowed) for allowed in _ALLOWED_IMAGE_HOSTS):
        raise HTTPException(status_code=400, detail="Image host not allowed")
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=10)
        resp.raise_for_status()
    except Exception:
        raise HTTPException(status_code=404, detail="Image not found")
    content_type = resp.headers.get("content-type", "image/png")
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="URL did not return an image")
    return Response(content=resp.content, media_type=content_type)
