from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import User as UserSchema, UserUpdate
from app.models import User as UserModel # at other place use app.models import User as User
from app.auth import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserSchema)
def get_user_me(current_user: UserModel = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user

@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user by ID
    """
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return db_user

@router.put("/me", response_model=UserSchema)
def update_user_me(
    user_update: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user information
    """
    # Get update data as dictionary
    try:
        update_data = user_update.model_dump(exclude_unset=True)
    except AttributeError:
        update_data = user_update.dict(exclude_unset=True)
    
    # Handle email update separately with explicit validation
    if "email" in update_data:
        new_email = update_data["email"]
        
        # Only check for duplicates if email is actually changing
        if new_email != current_user.email:
            # Explicit query for duplicate email
            duplicate_check = db.query(UserModel).filter(
                UserModel.email == new_email,
                UserModel.id != current_user.id  # Exclude current user
            ).first()
            
            # If duplicate found, RAISE 400 error immediately
            if duplicate_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
    
    # Apply updates to the user object
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    # Save to database
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user