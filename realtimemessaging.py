from flask import Flask, Request, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_socketio import join_room, leave_room
from flask_bcrypt import Bcrypt
import random
import string
import time
from flask import request
import hashlib



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'  # SQLite database file
app.config['SECRET_KEY'] = 'newanddkn84non23npibBIug87iG8uYDY6JVoiHgJ..df'
db = SQLAlchemy(app)
socketio = SocketIO(app)
bcrypt = Bcrypt(app)
active_chatrooms = {}


@app.route('/')
def index():
    return render_template('index.html')

# Define User and Chat models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.String(10), unique=True, nullable=False)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(10), nullable=False)
    chatroom_id = db.Column(db.String(200), nullable=False)
    message = db.Column(db.String(200), nullable=False)

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Hashed password
    agent_id = db.Column(db.String(10), unique=True, nullable=False)  # Add the agent_id field


# Create database tables within the application context
with app.app_context():
    db.create_all()

# Dummy agent data (for demonstration purposes)
# agents = [
#     {"username": "agent1", "password": "password1"},
#     {"username": "agent2", "password": "password2"},
# ]

# Sample route for creating a user
@app.route('/create_user', methods=['POST'])
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return 'User created successfully'

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Generate a random user ID
        user_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

        new_user = User(username=username, email=email, password=password, user_id=user_id)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login'))

    return render_template('signup.html')


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    user_id = session.get('user_id')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        chatroom_id = generate_chatroom_id(user_id) 
        chat_id = Chat(chatroom_id=chatroom_id)

        user = User.query.filter_by(username=username, password=password).first()

        if user and chat_id:
            # Store the user_id in the session
            session['user_id'] = user.user_id
            session['chatroom_id'] = chat_id.chatroom_id
            return redirect(url_for('index'))

        # If no matching user is found, show an error message
        error_message = "Invalid username or password. Please try again."
        return render_template('login.html', error_message=error_message)
    
   
    return render_template('login.html')

    
# Agent Login route
@app.route('/agentLogin', methods=['GET', 'POST'])
def agentLogin():
    agent_id = session.get('agent_id')

    if request.method == 'POST':
        username = request.form['agent_username']
        password = request.form['agent_password']

        agent = Agent.query.filter_by(username=username, password=password).first()

        if agent:
            # Store the agent_id in the session
            session['agent_id'] = agent.agent_id
            return redirect(url_for('dashboard'))

        # If no matching user is found, show an error message
        error_message = "Invalid username or password. Please try again."
        return render_template('agentLogin.html', error_message=error_message)

    return render_template('agentLogin.html')


#Agent Signup
@app.route('/agentSignup', methods=['GET', 'POST'])
def agentSignup():
    # agent_id = session.get('agent_id')

    if request.method == 'POST':
        username = request.form['agent_username']
        email = request.form['agent_email']
        password = request.form['agent_password']

        # Generate a random agent ID
        agent_id = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(10))

        new_agent = Agent(username=username, email=email, password=password, agent_id=agent_id)
        db.session.add(new_agent)
        db.session.commit()
        
        return redirect(url_for('agentLogin'))

    return render_template('agentSignup.html')

# Modify the dashboard function to accept chatroom_id as a parameter
@app.route('/dashboard/<chatroom_id>')
def dashboard(chatroom_id):
    # Retrieve chat history and user_id from the database
    user_id = session.get('user_id')
    chat_history = Chat.query.filter_by(chatroom_id=chatroom_id).all()
    return render_template('dashboard.html', chat_history=chat_history, user_id=user_id, chatroom_id=chatroom_id)


@socketio.on('message')
def handle_message(data):
    message = data['message']
    user_id = session.get('user_id')  # Retrieve the user ID from the session
    if user_id is not None:
        new_chat_message = Chat(user_id=user_id, message=message)
        db.session.add(new_chat_message)
        db.session.commit()
        emit('message', {'message': message}, broadcast=True)

# Route for sending a chat message
@app.route('/send_message', methods=['POST'])
def send_message():
    if request.method == 'POST':
        user_id = session.get('user_id')
        chatroom_id = request.form.get('chatroom_id')
        message = request.form.get('message')
        if user_id and chatroom_id:
            new_chat_message = Chat(user_id=user_id, chatroom_id=chatroom_id, message=message)
            db.session.add(new_chat_message)
            db.session.commit()
            return 'Message sent successfully'
    return 'Message sending failed.'


@app.route('/chat')
def chat():
    user_id = session.get('user_id')

        
    # def send_sms_alert(alert_message):
    #     url = "https://termii.com/api/sms/send"
    #     payload = {
    #         "to": "+2349076320678",
    #         "from": "Ogas",
    #         "sms": alert_message,  # Pass the alert message here
    #         "type": "plain",
    #         "channel": "generic",
    #         "api_key": "TLOQbYde8Vc9EGjHe9GxW0zPGkD50e8F9UpwDxHczn6UDCdbNJ6LRiHrUwf5nY",  # Replace with your actual Termii API key
    #     }
    #     headers = {
    #         'Content-Type': 'application/json',
    #     }
    #     response = Request.request("POST", url, headers=headers, json=payload)
    #     print(response.text)

    # # Function to simulate a chat with the customer
    # def chat_with_customer():
    #     print("Chatbot: Hello! I'm here to assist you.")
    #     time.sleep(3)

    #     # Ask for the customer's name
    #     customer_name = input("Chatbot: What's your name? ")
    #     time.sleep(1)

    #     # Ask if the customer is registered
    #     is_registered = input("Chatbot: Are you a registered customer? (Yes/No) ").lower()
    #     time.sleep(3)

    #     if is_registered == "yes":
    #         print(f"Chatbot: Welcome back, {customer_name}!")
    #     else:
    #         print(f"Chatbot: Hello, {customer_name}! Is there anything specific you'd like to know or discuss today?")
        
    #     # Offer some problem options (simplified)
    #     print("Chatbot: Here are some common problems:")
    #     print("1. Product not found")
    #     print("2. Payment issue")
    #     print("3. Shipping delay")
        
    #     # Ask the customer to select a problem or enter a custom problem
    #     problem_choice = input("Chatbot: Please select a problem number or describe your issue: ")
        
    #     # Handle the selected problem or custom problem (simplified)
    #     if problem_choice == "1":
    #         print("Chatbot: You can try searching for the product using our search feature.")
    #     elif problem_choice == "2":
    #         print("Chatbot: Please check your payment information and try again.")
    #     elif problem_choice == "3":
    #         print("Chatbot: We apologize for the delay. Your order should arrive soon.")
    #     else:
    #         print("Chatbot: I'm sorry, I couldn't understand your issue. Let me connect you to an agent.")

    #     # Simulate connecting to an agent with a timer (advanced)
    #     connection_time = 5  # Simulate a 5-second connection time
    #     for _ in range(connection_time):
    #         time.sleep(1)
    #         print(f"Chatbot: Connecting you to an agent... {connection_time} seconds remaining", end='\r')
    #         connection_time -= 1

    #     print("\nChatbot: Connected to an agent!")

    #     # Send an SMS alert with additional information
    #     alert_message = f"Hello! A customer ({customer_name}) needs assistance with the problem: {problem_choice}. Please connect to the chat."
    #     send_sms_alert(alert_message)
    #     print("Chatbot: Alert sent to the agent!")

    if user_id is None:
        return redirect(url_for('login'))

    return render_template('chat.html', user_id=user_id)

@app.route('/agentLogin', methods=['POST'])
def agent_authenticate():
    if request.method == 'POST':
        agent_username = request.form.get('agent_username')
        agent_password = request.form.get('agent_password')

        agent = Agent.query.filter_by(username=agent_username).first()

        if agent and bcrypt.check_password_hash(agent.password, agent_password):
            # Create a session for the authenticated agent
            session['agent_id'] = agent.id
            return jsonify({"message": "Agent authenticated successfully"}), 200
        else:
            return jsonify({"message": "Agent authentication failed"}), 401

def generate_chatroom_id(user_id):
    # Hash the user ID to create a unique chatroom ID
    chatroom_id = hashlib.md5(user_id.encode()).hexdigest()
    return chatroom_id

# Route to create a new chatroom based on user ID
@app.route('/create_chatroom/<user_id>')
def create_chatroom(user_id):
    chatroom = generate_chatroom_id(user_id)
    # Store the chatroom ID or use it as needed
    return f"Chatroom created with ID: {chatroom}"    

# Basic chatroom existence check (you may need to expand this)
def check_chatroom_exists(chatroom):
    return chatroom in active_chatrooms

@app.route('/enterChatroom')
def enter_chatroom():
    return render_template('enterChatroom.html')

# Route for agents to join a chatroom
@app.route('/enter_Chatroom', methods=['POST'])
def join_chatroom_form():
    chatroom_id = request.form.get('chatroom_id')
    agent_username = request.form.get('agent_username')

    # Check if the agent is authenticated
    authenticated = agent_authenticate(agent_username)

    if not authenticated:
        return "Agent not authenticated."

    # Check if the chatroom exists
    if check_chatroom_exists(chatroom_id):
        # If all checks pass, the agent can join the chatroom
        join_room(chatroom_id)
        active_chatrooms[chatroom_id] = agent_username  # Store the active chatroom and agent

        # You may want to notify the agent that they have successfully joined the chat
        # This notification can be sent through Flask-SocketIO
        socketio.emit('agent_joined', {'message': 'You have joined the chat.'}, room=chatroom_id)

        return "Joined chatroom successfully."
    else:
        return "Chatroom does not exist or is not available."

# Add a route for agents to leave chat rooms
@app.route('/leave_chatroom/<chatroom_id>/<agent_username>')
def leave_chatroom(chatroom_id, agent_username):
    # Check if the agent is authenticated (you may need to implement agent authentication)
    authenticated = agent_authenticate(agent_username)

    # Check if the agent is part of the chatroom
    if authenticated:
        if chatroom_id in active_chatrooms and active_chatrooms[chatroom_id] == agent_username:
            leave_room(chatroom_id)
            del active_chatrooms[chatroom_id]  # Remove the chatroom from the active list

            # You may want to notify the agent that they have successfully left the chat
            # This notification can be sent through Flask-SocketIO

            return "Left chatroom successfully"
        else:
            return "Agent not authorized to leave this chatroom"
    else:
        return "Agent not authenticated"



@app.route('/check_database')
def check_database():
    try:
        users = User.query.all()
        chats = Chat.query.all()
        agents = Agent.query.all()
        return f"Database connection successful. Users: {len(users)}, Chats: {len(chats)}, Agents: {len(agents)}"
    except Exception as e:
        return f"Database connection error: {str(e)}"

@app.route('/check_empty_database')
def check_empty_database():
    chats = Chat.query.all()
    if not chats:
        return "Database is empty"
    else:
        return "Database is not empty"


if __name__ == '__main__':
    socketio.run(app, debug=True)
