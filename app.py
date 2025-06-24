from flask import Flask, jsonify, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_socketio import SocketIO, emit, join_room, leave_room  # Import Flask-SocketIO
from db_setup import db, User, Project, Review,ChatRoom, Message 
import os
import random
from datetime import datetime

app = Flask(__name__)

# Flask-SocketIO setup
socketio = SocketIO(app)  # Initialize SocketIO


app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///builder_platform.db'
  # Update your database URI as needed
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')  # Folder to store uploaded images
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB
db.init_app(app)
migrate = Migrate(app, db)
# Create uploads directory if not exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash('Username or email already exists.', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        flash('Signup successful! Redirecting to login...', 'success')
        return redirect(url_for('login'))

    return render_template('reg.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/project/<int:project_id>', methods=['GET'])
def project_details(project_id):
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    
    project = Project.query.get_or_404(project_id)
    reviews = Review.query.filter_by(project_id=project_id).all()
    return render_template('project_details.html', project=project, reviews=reviews)

@app.route('/submit_review/<int:project_id>', methods=['POST'])
def submit_review(project_id):
    if 'user_id' not in session:
        flash('Please log in to submit a review', 'danger')
        return redirect(url_for('login'))

    review_content = request.form.get('review_content')
    if not review_content:
        flash('Review cannot be empty', 'warning')
        return redirect(url_for('project_details', project_id=project_id))
    
    new_review = Review(content=review_content, project_id=project_id, user_id=session['user_id'])
    db.session.add(new_review)
    db.session.commit()

    flash('Your review has been submitted!', 'success')
    return redirect(url_for('project_details', project_id=project_id))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        
        if 'image' not in request.files:
            flash('No file part in request', 'danger')
            return redirect(request.url)

        file = request.files['image']
        
        if file.filename == '':
            flash('No file selected', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            new_project = Project(
                name=name,
                description=description,
                price=float(price),
                image_path=f'uploads/{filename}',
                user_id=session['user_id']
            )
            db.session.add(new_project)
            db.session.commit()

            flash('Project added successfully!', 'success')
            return redirect(url_for('home'))

        else:
            flash('Invalid file format. Only JPEG allowed.', 'danger')
            return redirect(request.url)

    return render_template('add_product.html')

@app.route('/design_your_home')
def design_your_home():
    if 'user_id' not in session:
        flash('Please log in to access this page', 'danger')
        return redirect(url_for('login'))
    
    projects = Project.query.all()
    random_projects = random.sample(projects, min(10, len(projects)))
    project_ids = [p.id for p in random_projects]
    return render_template('design_home.html', projects=random_projects, project_ids=project_ids)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/chat/<int:project_id>', methods=['GET'])
def chat(project_id):
    """Route to access the chat room between user and uploader for a project."""
    if 'user_id' not in session:
        flash('Please log in to access the chat', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    project = Project.query.get_or_404(project_id)
    uploader_id = project.user_id  # The uploader is the one who created the project

    if user_id == uploader_id:
        flash("You can't chat with yourself in this project.", 'danger')
        return redirect(url_for('home'))

    # Find or create a unique chat room for this user and uploader pair for the specific project
    chat_room = ChatRoom.query.filter(
        (ChatRoom.project_id == project_id) &
        ((ChatRoom.user_id == user_id) & (ChatRoom.uploader_id == uploader_id) |
         (ChatRoom.user_id == uploader_id) & (ChatRoom.uploader_id == user_id))
    ).first()

    if not chat_room:
        # Create the chat room if it doesn't exist
        chat_room = ChatRoom(project_id=project_id, user_id=user_id, uploader_id=uploader_id)
        db.session.add(chat_room)
        db.session.commit()

    # Fetch messages for this chat room
    messages = Message.query.filter_by(chat_room_id=chat_room.id).all()

    return render_template('chat.html', project=project, chat_room=chat_room, messages=messages)


# SocketIO event to join a room
@socketio.on('join')
def handle_join(data):
    room = f"{data['user_id']}_{data['project_id']}"  # Use both user_id and project_id to define room
    join_room(room)
    emit('status', {'msg': f"{data['username']} has joined the room."}, room=room)

# SocketIO event to send a message
@socketio.on('send_message')
def handle_send_message(data):
    user_id = session.get('user_id')
    if user_id:
        # Save the message to the database
        message = Message(
            sender_id=user_id,
            receiver_id=data['receiver_id'],
            project_id=data['project_id'],
            message=data['message']
        )
        db.session.add(message)
        db.session.commit()

        # Define the room and emit message
        room = f"{user_id}_{data['project_id']}"  # Ensure room is based on user and project
        emit('receive_message', {
            'sender_id': user_id,
            'message': data['message'],
            'timestamp': message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }, room=room)


if __name__ == '__main__':
    socketio.run(app, debug=True)

# Ensure the database is created with the correct context
from db_setup import app, db  # Replace `your_flask_file` with the name of your main Flask file

with app.app_context():
    db.create_all()
