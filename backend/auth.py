from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

security = HTTPBearer()

def get_current_user_uid(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Decrypts and validates the Firebase ID Token (JWT) sent in the Authorization header.
    Returns the user's UID or raises 401 Unauthorized if invalid/expired.
    """
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token["uid"]
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired authentication token: {str(e)}"
        )
