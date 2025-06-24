from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from datetime import datetime, timedelta, timezone

# Create Flask app
app = Flask(__name__)

# Configure the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///builder_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy object
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)
# Define IST timezone
IST = timezone(timedelta(hours=5, minutes=30))
# Get the current time in IST
def get_ist_time():
    return datetime.now(IST)

# Define your models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    is_admin = db.Column(db.Boolean, default=False)  # New column for admin role

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # Foreign key to User
    user = db.relationship('User', backref=db.backref('projects', lazy=True))
    reviews = db.relationship('Review', backref='project', lazy=True)
    def __repr__(self):
        return f'<Project {self.name}>'


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Relationship to get user details
    user = db.relationship('User', backref='reviews', lazy=True)

class ChatRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    project = db.relationship('Project', backref='chat_rooms')
    user = db.relationship('User', foreign_keys=[user_id])
    uploader = db.relationship('User', foreign_keys=[uploader_id])
    messages = db.relationship('Message', backref='chat_room', lazy=True)

# Message model for storing messages within a chat room
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('chat_room.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', backref='messages')