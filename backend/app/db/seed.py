"""Seed cashier login only."""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models.user import User, Role
from app.db.session import SessionLocal

LOGIN_USER = "admin"
LOGIN_PASSWORD = "admin"
OLD_LOGINS = ("test", "salman", "cashier@demo.local")


def run_seed(db: Session | None = None) -> None:
    close = False
    if db is None:
        db = SessionLocal()
        close = True
    try:
        user = db.query(User).filter(User.email == LOGIN_USER).first()
        if not user:
            for old in OLD_LOGINS:
                user = db.query(User).filter(User.email == old).first()
                if user:
                    break
        if not user:
            user = User(name="Admin", email=LOGIN_USER, role=Role.CASHIER)
            db.add(user)

        user.name = "Admin"
        user.email = LOGIN_USER
        user.password_hash = hash_password(LOGIN_PASSWORD)
        user.role = Role.CASHIER
        db.commit()
        print(f"Seed complete. Login: {LOGIN_USER} / {LOGIN_PASSWORD}")
    finally:
        if close:
            db.close()


if __name__ == "__main__":
    run_seed()
