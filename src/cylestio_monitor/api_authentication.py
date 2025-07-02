"""API authentication for Cylestio Monitor.

This module provides authentication functionality for the Cylestio API client,
including JWT token generation using Descope.
"""

import logging
from typing import Optional

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
    
    def __init__(self, access_key: str, project_id: str = DESCOPE_PROJECT_ID) -> None:
        """Initialize the Descope authenticator.
        
        Args:
            project_id: The Descope project ID to use for authentication
        """
        self.project_id = project_id
        self._client: Optional[DescopeClient] = None
        self._access_key = access_key
        logger.debug(f"Initialized DescopeAuthenticator with project_id: {project_id} and access_key: {access_key}")
    
    def _get_client(self) -> DescopeClient:
        """Get the cached Descope client instance.
        
        Returns:
            DescopeClient: The cached Descope client instance
        """
        if self._client is None:
            self._client = DescopeClient(project_id=self.project_id)
            logger.debug("Created new Descope client instance")
        return self._client
    
    def get_jwt_token(self) -> Optional[str]:
        """Exchange an access key for a JWT token using Descope.

        Args:
            access_key: The access key to exchange for a JWT token

        Returns:
            Optional[str]: The JWT token if successful, None if failed
        """
        if not self._access_key:
            logger.error("Access key is required for JWT token exchange")
            return None

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
                    if jwt_token:
                        return jwt_token
                    else:
                        logger.error("JWT token not found in sessionToken")
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
