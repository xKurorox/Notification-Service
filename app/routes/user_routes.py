from app.database import get_db
from app.models import User
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.pydantic_schemas import UserRequest, UserResponse, UserUpdate
from typing import List
router = APIRouter()

# POST /users — create a user (email, phone, webhook_url, preferred_channel)
@router.post("/", response_model=UserResponse)
def create_user(request: UserRequest, db: Session = Depends(get_db)):
    exisiting_user = db.query(User).filter(User.email == request.email).first()
    if exisiting_user:
        raise HTTPException(status_code=409, detail="User already exist")
    new_user = User(email = request.email, phone = request.phone,
                webhook_url = request.webhook_url, preferred_channel = request.preferred_channel,
                email_enabled = request.email_enabled, sms_enabled = request.sms_enabled,
                webhook_enabled = request.webhook_enabled)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# GET /users — list all users
@router.get("/", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

# GET /users/{user_id} — get one user
@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# PUT /users/{user_id} — update a user's info
@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, request: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user

# DELETE /users/{user_id} — deactivate a user (set is_active to False, don't actually delete the row)
@router.delete("/{user_id}", response_model=UserResponse)
def del_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user