"""Authentication routes for Google OAuth 2.0."""
from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from models.preferences import UserPreferences
from services.auth_service import auth_service
from utils.security import generate_state_token, create_access_token
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/login")
async def login(request: Request):
    """
    Initiate Google OAuth login flow.
    
    Returns:
        Redirect to Google OAuth authorization URL
    """
    try:
        # Generate state token for CSRF protection
        state = generate_state_token()
        
        # Store state in session (in production, use secure session storage)
        request.session["oauth_state"] = state
        
        # Get authorization URL
        auth_url = auth_service.get_authorization_url(state)
        
        return RedirectResponse(url=auth_url)
    
    except Exception as e:
        logger.error(f"Error initiating login: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to initiate login")


@router.get("/callback")
async def callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from Google.
    
    Args:
        code: Authorization code
        state: State token for CSRF verification
        db: Database session
        
    Returns:
        Redirect to frontend with session token
    """
    try:
        # Verify state token
        stored_state = request.session.get("oauth_state")
        if not stored_state or stored_state != state:
            raise HTTPException(status_code=400, detail="Invalid state token")
        
        # Exchange code for token
        token_info = await auth_service.exchange_code_for_token(code)
        if not token_info:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        
        # Get user info
        user_info = await auth_service.get_user_info(token_info["access_token"])
        if not user_info:
            raise HTTPException(status_code=400, detail="Failed to get user info")
        
        # Check if user exists
        user = db.query(User).filter(User.google_id == user_info["google_id"]).first()
        
        if not user:
            # Create new user
            user = User(
                google_id=user_info["google_id"],
                email=user_info["email"],
                name=user_info["name"],
                profile_picture=user_info.get("profile_picture"),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create default preferences
            preferences = UserPreferences(user_id=user.id)
            db.add(preferences)
            db.commit()
        
        # Store OAuth credentials in session (in production, encrypt and store securely)
        request.session["user_id"] = user.id
        request.session["oauth_credentials"] = token_info
        
        # Create access token
        access_token = create_access_token({"sub": str(user.id)})
        
        # Redirect to frontend with token
        response = RedirectResponse(url=f"{settings.frontend_url}?token={access_token}")
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@router.post("/logout")
async def logout(request: Request):
    """
    Log out the current user.
    
    Returns:
        Success message
    """
    try:
        # Clear session
        request.session.clear()
        
        response = Response(content='{"message": "Logged out successfully"}', media_type="application/json")
        response.delete_cookie("access_token")
        
        return response
    
    except Exception as e:
        logger.error(f"Error logging out: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")


@router.get("/me")
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Get current authenticated user.
    
    Returns:
        User information
    """
    try:
        user_id = request.session.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user info")
