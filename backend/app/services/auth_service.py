from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.db.models.user import User
from app.schemas.auth import LoginResponse, UserOut


def authenticate(db: Session, email: str, password: str) -> LoginResponse | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    token = create_access_token(str(user.id), extra={"role": user.role.value})
    return LoginResponse(access_token=token, user=UserOut.model_validate(user))
