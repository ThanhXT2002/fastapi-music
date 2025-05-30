from fastapi import APIRouter, Depends, status
from app.api.controllers.auth import AuthController
from app.api.validators.auth import GoogleTokenRequest, AuthResponse

router = APIRouter()

@router.post(
    "/google",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with Google",
    description="Login or register a user with Google ID token"
)
def google_login(
    request: GoogleTokenRequest,
    auth_controller: AuthController = Depends()
) -> AuthResponse:
    return auth_controller.google_login(request.token)
