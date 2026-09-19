from app.database.database import SessionLocal
from app.repositories.user_repository import UserRepository


class UserService:
    def get_user(self, user_id: str) -> dict | None:
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            user = user_repo.find_by_id(user_id)
            if not user:
                return None
            return {
                "id": user.id,
                "username": user.username,
                "is_admin": user.is_admin,
            }
        finally:
            db.close()
