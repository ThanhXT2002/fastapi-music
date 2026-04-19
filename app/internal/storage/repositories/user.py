"""Repository quan ly tuong tac database cho Model User.

Module nay chua cac method CRUD co ban danh cho nguoi dung.
Xu ly session va exception tu SQLAlchemy.

Lien quan:
- Model: app/models/user.py
- Exceptions: app/models/errors.py
"""

# ── Standard library imports ──────────────────────────────
from typing import Optional, Dict, Any

# ── Third-party imports ───────────────────────────────────
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# ── Internal imports ──────────────────────────────────────
from app.models.user import User
from app.models.errors import UserNotFoundError


class UserRepository:
    """Class cung cap cac truy van tuong tac database cho User.

    Dong goi cac Session query thuong dung su dung trong
    Auth Controller hoac profile management.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_email(self, email: str) -> Optional[User]:
        """Tim kiem nguoi dung theo dia chi email.

        Args:
            email: Dia chi email cua nguoi dung.

        Returns:
            Doi tuong User neu tim thay, hoac None neu khong.
        """
        return self.db.query(User).filter(User.email == email).first()

    def find_by_uid(self, uid: str) -> Optional[User]:
        """Tim kiem nguoi dung theo Firebase UID.

        Args:
            uid: ID duoc tra ve tu Firebase Auth.

        Returns:
            Doi tuong User neu tim thay, hoac None neu khong.
        """
        return self.db.query(User).filter(User.id == uid).first()

    def create(self, user_data: Dict[str, Any]) -> User:
        """Tao va luu tru mot nguoi dung moi vao database.

        Args:
            user_data: Dict mapping cac field du lieu (email, name...).

        Returns:
            Doi tuong User vua duoc tao va refresh.

        Raises:
            IntegrityError: Neu email hoac thong tin bi trung,
                ham se tu dong rollback session truc tiep.
        """
        try:
            user = User(**user_data)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise

    def update(self, user_id: str, user_data: Dict[str, Any]) -> User:
        """Cap nhat thong tin nguoi dung theo ID.

        Args:
            user_id: ID cua nguoi dung trong database.
            user_data: Dict mapping cac thay doi can cap nhat.

        Returns:
            Doi tuong User sau khi cap nhat va refresh.

        Raises:
            UserNotFoundError: Neu khong ton tai user co ID tren.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        for key, value in user_data.items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user
