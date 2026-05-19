from sqlalchemy import Column, Float, ForeignKey, String
from database import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    set_code = Column(String, nullable=False)
    card_number = Column(String, nullable=False, unique=True)
    rarity = Column(String, nullable=False)
    character = Column(String, nullable=False)
    character_popularity = Column(String, nullable=False)
    story_relevance = Column(String, nullable=False)
    price_trend = Column(String, nullable=False)


class CardPrice(Base):
    __tablename__ = "card_prices"

    id = Column(String, primary_key=True)
    card_id = Column(String, ForeignKey("cards.id"), nullable=False)
    platform = Column(String, nullable=False)
    price_usd = Column(Float, nullable=False)
