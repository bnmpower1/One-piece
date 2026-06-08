from typing import Any
from pydantic import BaseModel


class PriceResponse(BaseModel):
    status: str
    data: dict[str, Any] | list | None = None
    message: str | None = None


class SuggestionResponse(BaseModel):
    status: str
    data: dict[str, Any] | list | None = None
    message: str | None = None
