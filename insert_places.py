from app import app
from extensions import db
from models import Place, PlaceImage

def insert_places():
    with app.app_context():
        # Optional: Clear existing Rajasthan & Kerala entries
        db.session.query(PlaceImage).delete()
        db.session.query(Place).filter(Place.state.in_(["Rajasthan", "Kerala"])).delete()
        db.session.commit()

        # Create Place entries
        jaipur = Place(name="Jaipur", description="The Pink City", state="Rajasthan")
        udaipur = Place(name="Udaipur", description="City of Lakes", state="Rajasthan")
        munnar = Place(name="Munnar", description="Tea Gardens and Hills", state="Kerala")
        alleppey = Place(name="Alleppey", description="Backwaters of Kerala", state="Kerala")

        db.session.add_all([jaipur, udaipur, munnar, alleppey])
        db.session.commit()

        # Add images after Place IDs are generated
        images = [
            PlaceImage(place_id=jaipur.id, filename="jaipur1.jpg"),
            PlaceImage(place_id=udaipur.id, filename="udaipur1.jpg"),
            PlaceImage(place_id=munnar.id, filename="munnar1.jpg"),
            PlaceImage(place_id=alleppey.id, filename="alleppey1.jpg"),
        ]

        db.session.add_all(images)
        db.session.commit()

        print("✅ Places and images inserted successfully.")

if __name__ == "__main__":
    insert_places()
