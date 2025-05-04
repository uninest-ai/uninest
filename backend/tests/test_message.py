import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import time
from datetime import datetime, timedelta

from app.main import app
from app.database import Base, get_db
from app.models import User, Message
from app.auth import create_access_token, get_password_hash

# Create a temporary in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency to use our test database
@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# Create test users
@pytest.fixture
def test_users(test_db):
    # Create two test users
    users = []
    for i, email in enumerate(["user1@example.com", "user2@example.com"]):
        hashed_password = get_password_hash("password123")
        user = User(
            email=email,
            username=f"testuser{i+1}",
            password_hash=hashed_password,
            user_type="tenant"
        )
        test_db.add(user)
    
    test_db.commit()
    users = test_db.query(User).all()
    return users

# Create tokens for test users
@pytest.fixture
def test_tokens(test_users):
    tokens = {}
    for user in test_users:
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=30)
        )
        tokens[user.id] = access_token
    return tokens

# Create test messages
@pytest.fixture
def test_messages(test_db, test_users):
    messages = []
    # Add some test messages between users
    for i in range(5):
        # User 1 sends messages to user 2
        message1 = Message(
            sender_id=test_users[0].id,
            receiver_id=test_users[1].id,
            content=f"Test message {i+1} from user1 to user2",
            timestamp=datetime.utcnow() - timedelta(minutes=10-i),
            is_read=False
        )
        # User 2 sends messages to user 1
        message2 = Message(
            sender_id=test_users[1].id,
            receiver_id=test_users[0].id,
            content=f"Test message {i+1} from user2 to user1",
            timestamp=datetime.utcnow() - timedelta(minutes=10-i),
            is_read=False
        )
        test_db.add(message1)
        test_db.add(message2)
        messages.extend([message1, message2])
    
    test_db.commit()
    # Refresh the messages to get their IDs
    for message in messages:
        test_db.refresh(message)
    
    return messages

# Test sending a message
def test_send_message(client, test_tokens, test_users):
    user1_id, user2_id = test_users[0].id, test_users[1].id
    token = test_tokens[user1_id]
    
    # Prepare the message data
    message_data = {
        "receiver_id": user2_id,
        "content": "Hello, this is a test message!"
    }
    
    # Send the message
    response = client.post(
        "/api/v1/messages/",
        json=message_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["sender_id"] == user1_id
    assert data["receiver_id"] == user2_id
    assert data["content"] == message_data["content"]
    assert data["is_read"] == False

# Test getting messages between two users
def test_get_messages(client, test_tokens, test_users, test_messages):
    user1_id, user2_id = test_users[0].id, test_users[1].id
    token = test_tokens[user1_id]
    
    # Get conversation with user2
    response = client.get(
        f"/api/v1/messages/?other_user_id={user2_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10  # 5 messages each way
    
    # Verify all messages are between user1 and user2
    for message in data:
        assert (message["sender_id"] == user1_id and message["receiver_id"] == user2_id) or \
               (message["sender_id"] == user2_id and message["receiver_id"] == user1_id)
    
    # Verify messages are ordered by timestamp
    timestamps = [message["timestamp"] for message in data]
    assert timestamps == sorted(timestamps)
    
    # Check that messages received by current user are now marked as read
    for message in data:
        if message["receiver_id"] == user1_id:
            assert message["is_read"] == True

# Test getting conversation list
def test_get_conversations(client, test_tokens, test_users, test_messages):
    user1_id = test_users[0].id
    token = test_tokens[user1_id]
    
    # Get conversations
    response = client.get(
        "/api/v1/messages/conversations",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1  # User1 has conversation with 1 other user
    
    conversation = data[0]
    assert conversation["user_id"] == test_users[1].id
    assert conversation["username"] == test_users[1].username
    assert "latest_message" in conversation
    assert "unread_count" in conversation

# Test marking a message as read
def test_mark_message_as_read(client, test_tokens, test_users, test_messages):
    user1_id = test_users[0].id
    token = test_tokens[user1_id]
    
    # Find a message sent from user2 to user1
    message = None
    for msg in test_messages:
        if msg.sender_id == test_users[1].id and msg.receiver_id == user1_id:
            message = msg
            break
    
    assert message is not None, "No message found from user2 to user1"
    
    # Mark message as read
    response = client.put(
        f"/api/v1/messages/{message.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == message.id
    assert data["is_read"] == True

# Test trying to mark someone else's message as read (should fail)
def test_mark_others_message_as_read(client, test_tokens, test_users, test_messages):
    user1_id = test_users[0].id
    token = test_tokens[user1_id]
    
    # Find a message sent from user1 to user2
    message = None
    for msg in test_messages:
        if msg.sender_id == user1_id and msg.receiver_id == test_users[1].id:
            message = msg
            break
    
    assert message is not None, "No message found from user1 to user2"
    
    # Try to mark message as read (should fail because user1 is not the receiver)
    response = client.put(
        f"/api/v1/messages/{message.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response - should be forbidden
    assert response.status_code == 403

# Test sending a message to non-existent user
def test_send_message_nonexistent_user(client, test_tokens, test_users):
    user1_id = test_users[0].id
    token = test_tokens[user1_id]
    
    # Prepare the message data with non-existent user ID
    message_data = {
        "receiver_id": 9999,  # Non-existent user ID
        "content": "This shouldn't work"
    }
    
    # Send the message
    response = client.post(
        "/api/v1/messages/",
        json=message_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Check response - should be not found
    assert response.status_code == 404