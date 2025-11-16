"""
Authentication API endpoints (dummy implementation)
"""
import logging
from fastapi import APIRouter, HTTPException
from src.models.schemas import AuthResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/dummy-login", response_model=AuthResponse)
async def dummy_login():
    """
    Dummy login endpoint for temporary authentication.
    
    Always succeeds and returns a dummy token.
    Future: Replace with SSO-based authentication.
    """
    logger.info("Dummy login request received")
    
    return AuthResponse(
        token="dummy_token_12345",
        expires="session",
        user={
            "id": "dummy_user",
            "name": "Anonymous User"
        }
    )


@router.get("/verify")
async def verify_token(
    token: str = None
):
    """
    Verify authentication token.
    
    For dummy implementation, accepts any token.
    Future: Implement proper JWT validation.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    
    # Dummy implementation: accept any token
    logger.info(f"Token verification request (dummy): {token[:20]}...")
    
    return {
        "valid": True,
        "user": {
            "id": "dummy_user",
            "name": "Anonymous User"
        }
    }
