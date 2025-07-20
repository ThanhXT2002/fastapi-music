from pydantic import BaseModel
from typing import Optional

class GoogleTokenRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    profile_picture: Optional[str]
    is_verified: Optional[bool]

class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserResponse
