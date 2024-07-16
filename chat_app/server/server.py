from flask import Flask, request, jsonify, session
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SESSION_TYPE'] = 'filesystem'
socketio = SocketIO(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1])
    return None

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        return jsonify({'message': 'User registered successfully!'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Username already exists!'}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_obj = User(id=user[0], username=user[1])
        login_user(user_obj)
        return jsonify({'message': 'Login successful!'}), 200
    else:
        return jsonify({'message': 'Invalid credentials!'}), 401

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful!'}), 200

@app.route('/add_friend', methods=['POST'])
@login_required
def add_friend():
    data = request.get_json()
    friend_username = data['friend_username']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username=?', (friend_username,))
    friend = cursor.fetchone()
    if friend:
        cursor.execute('INSERT INTO friends (user_id, friend_id) VALUES (?, ?)', (current_user.id, friend[0]))
        conn.commit()
        return jsonify({'message': 'Friend added successfully!'}), 201
    else:
        return jsonify({'message': 'User not found!'}), 404
    conn.close()

@app.route('/friends', methods=['GET'])
@login_required
def get_friends():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT u.id, u.username FROM friends f
                      JOIN users u ON f.friend_id = u.id
                      WHERE f.user_id = ?''', (current_user.id,))
    friends = cursor.fetchall()
    conn.close()
    return jsonify({'friends': [{'id': f[0], 'username': f[1]} for f in friends]})

@socketio.on('private_message')
@login_required
def handle_private_message(data):
    recipient_session_id = data['recipient_session_id']
    message = data['message']
    emit('private_message', {'message': message, 'sender': current_user.username}, room=recipient_session_id)

if __name__ == '__main__':
    def init_db():
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT NOT NULL UNIQUE,
                          password TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS friends (
                          user_id INTEGER,
                          friend_id INTEGER,
                          FOREIGN KEY(user_id) REFERENCES users(id),
                          FOREIGN KEY(friend_id) REFERENCES users(id))''')
        conn.commit()
        conn.close()

    init_db()
    socketio.run(app, debug=True)