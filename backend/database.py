from firebase_admin import firestore
from config import db

def get_session_history(session_id: str, user_uid: str) -> list:
    try:
        doc_ref = db.collection("users").document(user_uid).collection("conversations").document(session_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("messages", [])
    except Exception as e:
        print(f"Error fetching session history: {e}")
    return []

def save_session_history(session_id: str, messages: list, user_uid: str):
    try:
        doc_ref = db.collection("users").document(user_uid).collection("conversations").document(session_id)
        doc_ref.set({
            "messages": messages[-10:],
            "user_uid": user_uid,
            "updated_at": firestore.SERVER_TIMESTAMP
        }, merge=True)
    except Exception as e:
        print(f"Error saving session history: {e}")
