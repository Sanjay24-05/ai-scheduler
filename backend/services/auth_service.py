"""Authentication service for Google OAuth 2.0."""
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow
from typing import Optional, Dict
from config import settings
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling Google OAuth 2.0 authentication."""
    
    def __init__(self):
        """Initialize authentication service."""
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        
        # OAuth 2.0 scopes
        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/calendar',
        ]
    
    def get_authorization_url(self, state: str) -> str:
        """
        Generate Google OAuth authorization URL.
        
        Args:
            state: State token for CSRF protection
            
        Returns:
            Authorization URL
        """
        try:
            # Create flow instance
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            # Generate authorization URL
            authorization_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=state,
                prompt='consent'
            )
            
            return authorization_url
        
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Token information dictionary or None if error
        """
        try:
            # Create flow instance
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.redirect_uri],
                    }
                },
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            # Exchange code for token
            flow.fetch_token(code=code)
            
            # Get credentials
            credentials = flow.credentials
            
            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
            }
        
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            return None
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify Google ID token and extract user information.
        
        Args:
            token: Google ID token
            
        Returns:
            User information dictionary or None if invalid
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                self.client_id
            )
            
            # Extract user information
            return {
                "google_id": idinfo.get("sub"),
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "profile_picture": idinfo.get("picture"),
                "email_verified": idinfo.get("email_verified", False),
            }
        
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """
        Get user information from Google using access token.
        
        Args:
            access_token: Google access token
            
        Returns:
            User information dictionary or None if error
        """
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                response.raise_for_status()
                user_info = response.json()
                
                return {
                    "google_id": user_info.get("id"),
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "profile_picture": user_info.get("picture"),
                    "email_verified": user_info.get("verified_email", False),
                }
        
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None


# Global auth service instance
auth_service = AuthService()
