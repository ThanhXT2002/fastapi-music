from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.config.database import get_db
from app.config.config import settings
from app.internal.utils.helpers import verify_google_token
from app.internal.domain.errors import GoogleAuthError, UserNotFoundError
from app.internal.storage.repositories.user import UserRepository
from app.internal.rfc.jwt.jwt import create_access_token
from app.api.validators.auth import AuthResponse, TokenResponse, UserResponse

class AuthController:
    def __init__(self, db: Session = Depends(get_db)):
        self.user_repo = UserRepository(db)
        
    def google_login(self, token: str) -> AuthResponse:
        try:
            # Verify Google token
            user_info = verify_google_token(token)
            
            # Check if user exists
            user = self.user_repo.find_by_google_id(user_info['google_id'])
            
            if not user:
                # Find by email in case user registered with same email but different method
                user = self.user_repo.find_by_email(user_info['email'])
                
                if user:
                    # Update existing user with Google info
                    user = self.user_repo.update(user.id, {
                        'google_id': user_info['google_id'],
                        'is_verified': True,
                        'name': user_info.get('name', user.name),
                        'profile_picture': user_info.get('profile_picture', user.profile_picture)
                    })
                else:
                    # Create new user
                    user = self.user_repo.create({
                        'email': user_info['email'],
                        'name': user_info.get('name'),
                        'profile_picture': user_info.get('profile_picture'),
                        'google_id': user_info['google_id'],
                        'is_verified': True
                    })
            
            # Create access token
            token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            token = create_access_token(
                data={"sub": user.email}, 
                expires_delta=token_expires
            )
            
            return AuthResponse(
                token=TokenResponse(
                    access_token=token,
                    token_type="bearer"
                ),
                user=UserResponse(
                    id=user.id,
                    email=user.email,
                    name=user.name,
                    profile_picture=user.profile_picture,
                    is_verified=user.is_verified
                )
            )
            
        except GoogleAuthError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        except UserNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
