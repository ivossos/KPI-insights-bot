import json
import logging
from typing import Dict, Any, Optional
import urllib.parse
import requests
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.exceptions import RefreshError

from ..config import settings

logger = logging.getLogger(__name__)

class GoogleAuthenticator:
    """Handles Google OAuth authentication"""
    
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.scopes = [
            'openid',
            'email',
            'profile'
        ]
        
        # OAuth endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        
    def get_auth_url(self) -> str:
        """Generate authorization URL"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(self.scopes),
            'response_type': 'code',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        return f"{self.auth_url}?{urllib.parse.urlencode(params)}"
        
    def handle_callback(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """Handle OAuth callback and exchange code for tokens"""
        try:
            # Exchange code for tokens
            token_data = self._exchange_code_for_tokens(auth_code)
            
            if not token_data:
                logger.error("Failed to exchange code for tokens")
                return None
                
            # Get user info
            user_info = self._get_user_info(token_data['access_token'])
            
            if not user_info:
                logger.error("Failed to get user info")
                return None
                
            # Validate user
            if not self._validate_user(user_info):
                logger.warning(f"Unauthorized access attempt: {user_info.get('email', 'unknown')}")
                return None
                
            # Store credentials
            self._store_credentials(user_info['email'], token_data)
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {str(e)}")
            return None
            
    def _exchange_code_for_tokens(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access tokens"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging code for tokens: {str(e)}")
            return None
            
    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Google"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(self.userinfo_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"User info request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            return None
            
    def _validate_user(self, user_info: Dict[str, Any]) -> bool:
        """Validate if user is authorized"""
        email = user_info.get('email', '')
        
        # Check if email is from authorized domain
        authorized_domains = ['capivari.sp.gov.br', 'gmail.com']  # Add authorized domains
        authorized_emails = [
            'admin@capivari.sp.gov.br',
            'auditoria@capivari.sp.gov.br',
            'fiscal@capivari.sp.gov.br'
        ]
        
        # Check domain or specific email
        domain = email.split('@')[1] if '@' in email else ''
        
        return domain in authorized_domains or email in authorized_emails
        
    def _store_credentials(self, email: str, token_data: Dict[str, Any]) -> None:
        """Store user credentials securely"""
        try:
            # In a real implementation, store in database
            # For now, just log the successful authentication
            logger.info(f"User authenticated: {email}")
            
            # Store token data with expiration
            expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
            
            credential_data = {
                'email': email,
                'access_token': token_data.get('access_token'),
                'refresh_token': token_data.get('refresh_token'),
                'expires_at': expires_at.isoformat(),
                'authenticated_at': datetime.now().isoformat()
            }
            
            # In production, store in secure database
            # For now, just log successful storage
            logger.info(f"Credentials stored for {email}")
            
        except Exception as e:
            logger.error(f"Error storing credentials: {str(e)}")
            
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token using refresh token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(self.token_url, data=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
            
    def verify_token(self, access_token: str) -> bool:
        """Verify if access token is valid"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(self.userinfo_url, headers=headers)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return False
            
    def get_user_roles(self, email: str) -> list:
        """Get user roles based on email"""
        admin_emails = [
            'admin@capivari.sp.gov.br',
            'auditoria@capivari.sp.gov.br'
        ]
        
        if email in admin_emails:
            return ['admin', 'user']
        else:
            return ['user']
            
    def logout(self, access_token: str) -> bool:
        """Logout user and revoke tokens"""
        try:
            # Revoke token
            revoke_url = f"https://oauth2.googleapis.com/revoke?token={access_token}"
            
            response = requests.post(revoke_url)
            
            if response.status_code == 200:
                logger.info("Token revoked successfully")
                return True
            else:
                logger.warning(f"Token revocation failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return False
            
    def check_session_validity(self, user_session: Dict[str, Any]) -> bool:
        """Check if user session is still valid"""
        try:
            expires_at = datetime.fromisoformat(user_session.get('expires_at', ''))
            
            if datetime.now() >= expires_at:
                # Try to refresh token
                refresh_token = user_session.get('refresh_token')
                if refresh_token:
                    new_tokens = self.refresh_token(refresh_token)
                    if new_tokens:
                        # Update session with new tokens
                        user_session['access_token'] = new_tokens.get('access_token')
                        user_session['expires_at'] = (
                            datetime.now() + timedelta(seconds=new_tokens.get('expires_in', 3600))
                        ).isoformat()
                        return True
                
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking session validity: {str(e)}")
            return False
            
    def get_user_permissions(self, email: str) -> Dict[str, bool]:
        """Get user permissions based on role"""
        roles = self.get_user_roles(email)
        
        permissions = {
            'view_alerts': True,
            'investigate_alerts': True,
            'export_data': True,
            'view_reports': True,
            'manage_settings': 'admin' in roles,
            'manage_users': 'admin' in roles,
            'view_logs': 'admin' in roles
        }
        
        return permissions