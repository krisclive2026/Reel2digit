from sqlalchemy.orm import Session
from app.models import PricingConfig

def get_pricing_config(db: Session) -> PricingConfig:
    config = db.query(PricingConfig).first()
    if not config:
        config = PricingConfig(unit_price=15.00, shipping_flat=8.99, max_cassettes=50)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def calculate_order_price(count: int, unit_price: float, shipping_flat: float) -> dict:
    subtotal = round(count * unit_price, 2)
    shipping = round(shipping_flat, 2)
    total = round(subtotal + shipping, 2)
    return {
        "count": count,
        "unit_price": unit_price,
        "subtotal": subtotal,
        "shipping": shipping,
        "total": total
    }
