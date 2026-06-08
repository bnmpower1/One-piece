import hashlib
import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/ebay", tags=["ebay"])


@router.get("/account-deletion")
def ebay_challenge(challenge_code: str):
    verification_token = os.getenv("EBAY_VERIFICATION_TOKEN", "")
    endpoint_url = os.getenv("EBAY_ENDPOINT_URL", "")

    hash_input = challenge_code + verification_token + endpoint_url
    challenge_response = hashlib.sha256(hash_input.encode()).hexdigest()

    return JSONResponse(content={"challengeResponse": challenge_response})


@router.post("/account-deletion")
async def account_deletion(request: Request):
    # We don't store any eBay user data, so no deletion action needed.
    # eBay requires this endpoint to exist and return 200.
    return JSONResponse(content={"status": "ok"})
