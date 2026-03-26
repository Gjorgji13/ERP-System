# auth.py
from models.user_model import get_user


def authenticate(username: str, password: str):
    user = get_user(username)
    print("DEBUG USER:", user)

    if not user:
        return None

    print("DEBUG PASSWORD INPUT:", password)
    print("DEBUG PASSWORD STORED:", user["password"])

    if user["password"] != password:
        return None

    return user