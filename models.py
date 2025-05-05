
from flask_login import UserMixin
from extensions import db
from datetime import datetime

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)  # Add name field
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_paths = db.Column(db.Text, nullable=False)  # Comma-separated
    uploader_email = db.Column(db.String(150), nullable=False) 
    # user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
# Initialize database

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    state = db.Column(db.String(100))
    images = db.relationship('PlaceImage', backref='place', lazy=True)
    rating = db.Column(db.Float, default=0.0)

class PlaceImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)

class LikedPlace(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100), db.ForeignKey('user.email'), nullable=False)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)

    user = db.relationship('User', backref='liked_places')
    place = db.relationship('Place', backref='liked_by')

# Rating model
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    user_email = db.Column(db.String(150), nullable=False)
    stars = db.Column(db.Integer, nullable=False)

# Feedback model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), nullable=False)
    user_email = db.Column(db.String(150), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

