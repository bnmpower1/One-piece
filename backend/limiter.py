from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

GEMINI_RATE_LIMIT = "10/minute"
GEMINI_DAILY_LIMIT = "50/day"
