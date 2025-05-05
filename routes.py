from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import login_required, LoginManager, current_user, login_user
from app import app
from extensions import db
from werkzeug.security import check_password_hash
from models import User, Post, Place, PlaceImage, LikedPlace, Rating, Feedback
import uuid
import bcrypt
import os
import requests

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Redirect to login page if not logged in

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html", page="register")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Check if the email is already registered
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("User already exists with this email!", "error")
            return render_template("index.html", page="register")

        # Hash the password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        # Create a new user with the name, email, and hashed password
        new_user = User(name=name, email=email, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()  # Rollback in case of error
            flash("An error occurred while saving the user.", "error")
            return render_template("index.html", page="register")

        return redirect(url_for("login"))

    return render_template("index.html", page="register")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Fetch the user from the database using email
        user = User.query.filter_by(email=email).first()

        # Validate the user's password
        if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            login_user(user)  # Login the user
            return redirect(url_for("home"))
        else:
            flash("Invalid email or password. Please try again.", "error")
            return redirect(url_for("login"))

    return render_template("index.html", page="login")

@app.route("/home")
def home():
    return render_template("home.html", page="home")

@app.route("/logout")
def logout():
    return redirect(url_for("login"))

@app.route("/india", endpoint="india")
def file1():
    return render_template("india.html")

@app.route("/gallery", endpoint="gallery")
def file2():
    return render_template("gallery.html")

@app.route('/hiddengems')
def hiddengems():
    posts = Post.query.all()
    return render_template('hiddengems.html', posts=posts, current_email=current_user.email)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        place_name = request.form.get('name')
        description = request.form.get('description')
        files = request.files.getlist('images')

        if not place_name or not description:
            flash("Please provide a name and description.", "error")
            return redirect(url_for('upload'))

        image_paths = []
        for file in files:
            if file:
                unique_filename = f"{uuid.uuid4()}_{file.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(filepath)
                image_paths.append(unique_filename)

        # Save post to database
        new_post = Post(
            name=place_name,
            description=description,
            image_paths=",".join(image_paths),
            uploader_email=current_user.email
        )
        try:
            db.session.add(new_post)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while saving the post.", "error")
            return redirect(url_for('upload'))

        return redirect(url_for('hiddengems'))

    return render_template('upload.html')

@app.route("/uploads/<filename>")
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/delete/<int:post_id>", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.uploader_email != current_user.email:
        flash("You do not have permission to delete this post.", "error")
        return redirect(url_for("hiddengems"))

    if post.image_paths:
        image_paths = post.image_paths.split(",")
        for path in image_paths:
            try:
                os.remove(os.path.join(app.config["UPLOAD_FOLDER"], path))
            except FileNotFoundError:
                pass

    try:
        db.session.delete(post)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the post.", "error")

    return redirect(url_for("hiddengems"))

@app.route('/state/<state_name>')
def state(state_name):
    places = Place.query.filter_by(state=state_name).all()
    places_data = []

    for place in places:
        images = [img.filename for img in place.images]
        ratings = Rating.query.filter_by(place_id=place.id).all()
        avg_rating = sum(r.stars for r in ratings) / len(ratings) if ratings else 0.0
        feedbacks = Feedback.query.filter_by(place_id=place.id).all()

        places_data.append({
            'place': place,
            'images': images,
            'avg_rating': avg_rating,
            'feedbacks': feedbacks
        })

    return render_template('state.html', state_name=state_name, places_data=places_data, current_email=current_user.email)

@app.route('/liked', methods=['GET', 'POST'])
@login_required
def liked_places():
    if request.method == 'POST':
        place_id = request.json.get('place_id')
        if not place_id:
            return jsonify({'success': False, 'error': 'No place ID provided'}), 400

        liked_place = LikedPlace.query.filter_by(user_email=current_user.email, place_id=place_id).first()
        if liked_place:
            db.session.delete(liked_place)
            db.session.commit()
            return jsonify({'success': True, 'liked': False})
        else:
            new_like = LikedPlace(user_email=current_user.email, place_id=place_id)
            db.session.add(new_like)
            db.session.commit()
            return jsonify({'success': True, 'liked': True})

    liked_places = LikedPlace.query.filter_by(user_email=current_user.email).all()
    places_data = []

    for liked_place in liked_places:
        place = liked_place.place
        ratings = Rating.query.filter_by(place_id=place.id).all()
        avg_rating = round(sum(r.stars for r in ratings) / len(ratings), 1) if ratings else 0.0
        feedbacks = Feedback.query.filter_by(place_id=place.id).all()

        places_data.append({
            'id': place.id,
            'name': place.name,
            'description': place.description,
            'images': [img.filename for img in place.images],
            'rating': avg_rating,
            'feedbacks': feedbacks
        })

    return render_template('liked.html', places_data=places_data, current_email=current_user.email)

@app.route('/toggle_like/<int:place_id>', methods=['POST'])
@login_required
def toggle_like(place_id):
    existing = LikedPlace.query.filter_by(user_email=current_user.email, place_id=place_id).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
    else:
        new_like = LikedPlace(user_email=current_user.email, place_id=place_id)
        db.session.add(new_like)
        db.session.commit()

    return redirect(url_for('liked_places'))

@app.route('/submit_rating_feedback/<int:place_id>', methods=['POST'])
@login_required
def submit_rating_feedback(place_id):
    rating_value = request.form.get('rating')
    feedback_comment = request.form.get('feedback')

    if rating_value:
        existing_rating = Rating.query.filter_by(user_email=current_user.email, place_id=place_id).first()
        if existing_rating:
            existing_rating.stars = int(rating_value)
        else:
            new_rating = Rating(user_email=current_user.email, place_id=place_id, stars=int(rating_value))
            db.session.add(new_rating)

    if feedback_comment and feedback_comment.strip():
        new_feedback = Feedback(user_email=current_user.email, place_id=place_id, comment=feedback_comment.strip())
        db.session.add(new_feedback)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while submitting your rating/feedback.", "error")

    return redirect(request.referrer)

@app.route('/delete_feedback_and_rating/<int:place_id>', methods=['POST'])
@login_required
def delete_feedback_and_rating(place_id):
    feedback_id = request.form.get('feedback_id')
    feedback = Feedback.query.get(feedback_id)

    if not feedback:
        flash("Feedback not found.", "error")
        return redirect(request.referrer)

    if feedback.user_email != current_user.email:
        flash("You do not have permission to delete this feedback.", "error")
        return redirect(request.referrer)

    try:
        db.session.delete(feedback)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting feedback.", "error")

    return redirect(request.referrer)
