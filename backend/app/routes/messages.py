from fastapi import APIRouter, Depends, HTTPException, status, Body, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from jose import jwt, JWTError

from app.database import get_db
from app.models import User, Message
from app.schemas import MessageCreate, MessageResponse, MessageUpdate
from app.auth import get_current_user
from app.config import settings

router = APIRouter()

active_connections = {}

@router.post("/", response_model=MessageResponse)
async def send_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message to another user
    """
    # Check if receiver exists
    receiver = db.query(User).filter(User.id == message.receiver_id).first()
    if not receiver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Receiver not found"
        )
    
    # Create new message
    db_message = Message(
        sender_id=current_user.id,
        receiver_id=message.receiver_id,
        content=message.content,
        is_read=False
    )
    
    # Save to database
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    #send to WebSocket
    room_id = f"{min(current_user.id, message.receiver_id)}_{max(current_user.id, message.receiver_id)}"
    msg_data = {
        "content": db_message.content,
        "sender_id": db_message.sender_id,
        "receiver_id": db_message.receiver_id,
        "timestamp": db_message.timestamp.isoformat(),
        "id": db_message.id,
    }
    for ws in active_connections.get(room_id, []):
        await ws.send_text(json.dumps(msg_data))

    return db_message

@router.get("/", response_model=List[MessageResponse])
def get_messages(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get conversation history with another user
    """
    # Check if other user exists
    other_user = db.query(User).filter(User.id == other_user_id).first()
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get messages between current user and other user
    messages = db.query(Message).filter(
        (
            (Message.sender_id == current_user.id) & 
            (Message.receiver_id == other_user_id)
        ) | (
            (Message.sender_id == other_user_id) & 
            (Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp).all()
    
    # Mark messages as read
    for msg in messages:
        if msg.receiver_id == current_user.id and not msg.is_read:
            msg.is_read = True
    
    db.commit()
    
    return messages

@router.get("/conversations", response_model=List[dict])
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users the current user has conversed with
    """
    # Get all unique users the current user has exchanged messages with
    sent_to = db.query(Message.receiver_id).filter(
        Message.sender_id == current_user.id
    ).distinct().all()
    
    received_from = db.query(Message.sender_id).filter(
        Message.receiver_id == current_user.id
    ).distinct().all()
    
    # Combine and remove duplicates
    user_ids = set([uid[0] for uid in sent_to + received_from])
    
    # Get user details and latest message for each conversation
    conversations = []
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Get the latest message in this conversation
            latest_message = db.query(Message).filter(
                (
                    (Message.sender_id == current_user.id) & 
                    (Message.receiver_id == user_id)
                ) | (
                    (Message.sender_id == user_id) & 
                    (Message.receiver_id == current_user.id)
                )
            ).order_by(Message.timestamp.desc()).first()
            
            # Count unread messages
            unread_count = db.query(Message).filter(
                Message.sender_id == user_id,
                Message.receiver_id == current_user.id,
                Message.is_read == False
            ).count()
            
            conversations.append({
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "latest_message": {
                    "content": latest_message.content,
                    "timestamp": latest_message.timestamp,
                    "is_sent_by_me": latest_message.sender_id == current_user.id
                },
                "unread_count": unread_count
            })
    
    # Sort by latest message timestamp
    conversations.sort(
        key=lambda x: x["latest_message"]["timestamp"], 
        reverse=True
    )
    
    return conversations

@router.put("/{message_id}", response_model=MessageResponse)
def mark_message_as_read(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a message as read
    """
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Check if current user is the receiver
    if message.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to mark this message as read"
        )
    
    # Mark as read
    message.is_read = True
    db.commit()
    db.refresh(message)
    
    return message

async def get_user_from_token(token: str, db):
    print("Token received:", token)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        print("Decoded payload:", payload)
        email: str = payload.get("sub")
        if email is None:
            print("No sub in token payload")
            return None
        user = db.query(User).filter(User.email == email).first()
        print("User found:", user)
        return user
    except JWTError as e:
        print("JWTError:", e)
        return None

@router.websocket("/ws/{other_user_id}")
async def websocket_endpoint(websocket: WebSocket, other_user_id: int, db: Session = Depends(get_db)):
    
    print("WebSocket endpoint called")
    await websocket.accept()
    token = websocket.query_params.get("token")
    user = await get_user_from_token(token, db)
    if not user:
        print("WebSocket auth failed, closing connection.")
        await websocket.close(code=1008,reason="Authentication failed")
        return
    print("WebSocket auth success, user:", user.email)
    room_id = f"{min(user.id, other_user_id)}_{max(user.id, other_user_id)}"
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()  
    except WebSocketDisconnect:
        active_connections[room_id].remove(websocket)
