from app.database import engine, Base, SessionLocal
from app.models import PricingConfig, User
from app.auth import hash_password

def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check PricingConfig
        config = db.query(PricingConfig).first()
        if not config:
            config = PricingConfig(unit_price=15.00, shipping_flat=8.99, max_cassettes=50)
            db.add(config)
            print("Seeded PricingConfig (₹15.00/cassette, ₹8.99 shipping, max 50).")

        # Check Default Admin
        admin = db.query(User).filter(User.email == "admin@reeltodigit.com").first()
        if not admin:
            admin = User(
                email="admin@reeltodigit.com",
                hashed_password=hash_password("Admin123!"),
                full_name="ReelToDigit Admin",
                phone="555-0199",
                street_address="100 Lab Storage Way",
                city="San Jose",
                state="CA",
                postal_code="95110",
                country="USA",
                role="admin"
            )
            db.add(admin)
            print("Seeded Default Admin: admin@reeltodigit.com / Admin123!")

        # Check Default Customer
        demo_user = db.query(User).filter(User.email == "customer@example.com").first()
        if not demo_user:
            demo_user = User(
                email="customer@example.com",
                hashed_password=hash_password("Customer123!"),
                full_name="Jane Customer",
                phone="555-0123",
                street_address="742 Evergreen Terrace",
                city="Springfield",
                state="IL",
                postal_code="62701",
                country="USA",
                role="customer"
            )
            db.add(demo_user)
            print("Seeded Default Customer: customer@example.com / Customer123!")

        db.commit()
        print("Database seeding completed successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
