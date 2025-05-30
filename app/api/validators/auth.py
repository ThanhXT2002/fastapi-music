from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class GoogleTokenRequest(BaseModel):
    token: str = Field(..., description="Google ID token")
    
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: Optional[str] = None
    profile_picture: Optional[str] = None
    is_verified: bool
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserResponse
    
    class Config:
        from_attributes = True
