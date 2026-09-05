import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

security = HTTPBearer()

def get_current_user_uid(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Decrypts and validates the Firebase ID Token (JWT) sent in the Authorization header.
    If running on the Gemma service (SERVICE_NAME=backend-gemma), strictly enforces
    that the caller possesses the sre_genai_admin custom claim (403 Forbidden).
    Returns the user's UID or raises 401 Unauthorized if invalid/expired.
    """
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired authentication token: {str(e)}"
        )

    # Zero-trust enforcement on backend-gemma
    is_gemma_service = os.getenv("SERVICE_NAME") == "backend-gemma" or os.getenv("K_SERVICE") == "backend-gemma"
    if is_gemma_service and not decoded_token.get("sre_genai_admin"):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: sre_genai_admin role claim required to access Gemma inference."
        )

    return decoded_token["uid"]


def require_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verifies that the caller has a valid Firebase ID Token with the sre_genai_admin custom claim.
    Returns the admin user's UID or raises 403 Forbidden / 401 Unauthorized.
    """
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        if not decoded_token.get("sre_genai_admin"):
            raise HTTPException(
                status_code=403,
                detail="Forbidden: sre_genai_admin role claim required."
            )
        return decoded_token["uid"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired authentication token: {str(e)}"
        )

