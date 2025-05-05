from app import app
from extensions import db
from models import Place, PlaceImage

def delete_all_places():
    with app.app_context():
        # Delete all PlaceImage and Place data
        db.session.query(PlaceImage).delete()
        db.session.query(Place).delete()
        db.session.commit()
        print("🗑️ All places and their images deleted.")

if __name__ == "__main__":
    delete_all_places()
