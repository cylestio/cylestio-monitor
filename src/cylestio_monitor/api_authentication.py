"""API authentication for Cylestio Monitor.

This module provides authentication functionality for the Cylestio API client,
including JWT token generation using Descope.
"""

import logging
import time
from typing import Optional, Dict

from descope import AuthException, DescopeClient

# Configure logging
logger = logging.getLogger("cylestio_monitor.api_authentication")

# Descope configuration
DESCOPE_PROJECT_ID = 'P2zF0Fh3eZsfOBM2cqh03EPfa6G4'


class DescopeAuthenticator:
    """Descope authentication client with instance caching.
    
    This class provides JWT token exchange functionality using Descope,
    with a cached Descope client instance for improved performance.
    """
    
    # Class-level cache for singleton instances by access_key
    _instances: Dict[str, 'DescopeAuthenticator'] = {}
    
    def __init__(self, access_key: str, project_id: str = DESCOPE_PROJECT_ID, refresh_buffer_seconds: int = 30) -> None:
        """Initialize the Descope authenticator.
        
        Args:
            access_key: The access key to use for authentication
            project_id: The Descope project ID to use for authentication
            refresh_buffer_seconds: Seconds before expiration to refresh token (default: 30)
        """
        self.project_id = project_id
        self._client: Optional[DescopeClient] = None
        self._access_key = access_key
        self._refresh_buffer_seconds = refresh_buffer_seconds
        
        # Token caching
        self._cached_jwt_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        
        logger.debug(f"Initialized DescopeAuthenticator with project_id: {project_id} and access_key: {access_key}")
    
    @classmethod
    def get_instance(cls, access_key: str, project_id: str = DESCOPE_PROJECT_ID, refresh_buffer_seconds: int = 30) -> 'DescopeAuthenticator':
        """Get a singleton instance of DescopeAuthenticator for the given access_key.
        
        Args:
            access_key: The access key to use for authentication
            project_id: The Descope project ID to use for authentication
            refresh_buffer_seconds: Seconds before expiration to refresh token (default: 30)
            
        Returns:
            DescopeAuthenticator: Singleton instance for the access_key
        """
        if access_key not in cls._instances:
            cls._instances[access_key] = cls(access_key, project_id, refresh_buffer_seconds)
        return cls._instances[access_key]
    
    def _get_client(self) -> DescopeClient:
        """Get the cached Descope client instance.
        
        Returns:
            DescopeClient: The cached Descope client instance
        """
        if self._client is None:
            self._client = DescopeClient(project_id=self.project_id)
            logger.debug("Created new Descope client instance")
        return self._client
    
    def _is_token_expired(self) -> bool:
        """Check if the cached token is expired or about to expire.
        
        Returns:
            bool: True if token is expired or expires within refresh_buffer_seconds, False otherwise
        """
        if self._token_expires_at is None:
            return True
        
        # Check if token expires within the buffer time
        is_token_expired = time.time() >= (self._token_expires_at - self._refresh_buffer_seconds)
        if is_token_expired:
            logger.info("JWT token expired, forcing a fresh exchange on next call")
        return is_token_expired
    
    def invalidate_token(self) -> None:
        """Invalidate the cached JWT token, forcing a fresh exchange on next call.
        
        This method clears the cached token and expiration time. Useful when 
        authentication errors occur and you need to force token renewal.
        """
        self._cached_jwt_token = None
        self._token_expires_at = None
        logger.debug("JWT token cache invalidated")
    
    def get_jwt_token(self) -> Optional[str]:
        """Exchange an access key for a JWT token using Descope.

        Returns cached token if still valid, otherwise exchanges access key for new token.

        Returns:
            Optional[str]: The JWT token if successful, None if failed
        """
        if not self._access_key:
            logger.error("Access key is required for JWT token exchange")
            return None

        # Return cached token if still valid
        if self._cached_jwt_token and not self._is_token_expired():
            return self._cached_jwt_token

        try:
            # Exchange access key for JWT using cached client
            resp = self._get_client().exchange_access_key(access_key=self._access_key)
            logger.debug("Successfully exchanged access key for JWT token")
            
            # Extract the JWT token from the response
            if isinstance(resp, dict):
                # Based on actual response structure: response['sessionToken']['jwt']
                session_token = resp.get('sessionToken')
                if isinstance(session_token, dict):
                    jwt_token = session_token.get('jwt')
                    token_exp = session_token.get('exp')
                    
                    if jwt_token and token_exp:
                        # Cache the token and expiration
                        self._cached_jwt_token = jwt_token
                        self._token_expires_at = float(token_exp)
                        
                        logger.info(f"Refreshed token, updating cache, expires at: {time.ctime(self._token_expires_at)}")
                        return jwt_token
                    else:
                        logger.error("JWT token or expiration not found in sessionToken")
                        return None
                else:
                    logger.error("sessionToken not found or invalid in response")
                    logger.debug(f"Available response keys: {list(resp.keys())}")
                    return None
            else:
                logger.error(f"Unexpected response type: {type(resp)}")
                return None
                
        except AuthException as e:
            logger.error(f"Unable to exchange access key for JWT. Status: {e.status_code}, Error: {e.error_message}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error occurred during JWT token exchange: {e}")
            return None


__all__ = ["DescopeAuthenticator"]
