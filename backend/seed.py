import json
from database import Base, SessionLocal, engine
from models import Card, CardPrice

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    with open("seed_data.json") as f:
        cards = json.load(f)

    for entry in cards:
        if db.query(Card).filter(Card.id == entry["id"]).first():
            continue

        card = Card(
            id=entry["id"],
            name=entry["name"],
            set_code=entry["set_code"],
            card_number=entry["card_number"],
            rarity=entry["rarity"],
            character=entry["character"],
            character_popularity=entry["character_popularity"],
            story_relevance=entry["story_relevance"],
            price_trend=entry["price_trend"],
        )
        db.add(card)

        for platform, price in entry["prices"].items():
            price_record = CardPrice(
                id=f"{entry['id']}_{platform.lower()}",
                card_id=entry["id"],
                platform=platform,
                price_usd=price,
            )
            db.add(price_record)

    db.commit()
    db.close()
    print("Seeded database.")


if __name__ == "__main__":
    seed()
