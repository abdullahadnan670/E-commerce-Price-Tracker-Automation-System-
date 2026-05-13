from pydantic import BaseModel, EmailStr
from typing import Optional

# 1. Used when a user signs up
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# 2. Used when returning user data (we NEVER return the password)
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    class Config:
        from_attributes = True

# 3. Used for the Login Token
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None