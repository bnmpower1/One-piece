from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from database import Base, engine
from limiter import limiter
from routers import cards, suggestions
from seed import seed

Base.metadata.create_all(bind=engine)
seed()

app = FastAPI(title="One Piece Card Tracker")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(cards.router)
app.include_router(suggestions.router)


@app.get("/")
def root():
    return {"message": "One Piece Card Tracker API"}
