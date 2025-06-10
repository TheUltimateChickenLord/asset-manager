# pylint: disable=consider-using-in, singleton-comparison
"""Module defining the class to perform CRUD operations on Users"""

from typing import Any, Optional

from asset_manager.core.security import hash_password
from asset_manager.db.models.user import User
from asset_manager.repositories.abstract_crud_repo import AbstractCRUDRepo


class UserRepository(AbstractCRUDRepo[User]):
    """A class to perform CRUD operations on the repository of Users in the database"""

    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by their email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_name(self, name: str) -> Optional[User]:
        """Get a user by their name"""
        return self.db.query(User).filter(User.name == name).first()

    def register_user(self, name: str, email: str, password: str) -> User:
        """Create a new user and store their password hash"""
        hashed_pw, salt = hash_password(password)
        user = User(name=name, email=email, password_hash=hashed_pw, password_salt=salt)
        return self.create(user)

    def disable_user(self, user: User) -> User:
        """Disable a users account"""
        return self.update(user, {"is_disabled": True})

    def enable_user(self, user: User) -> User:
        """Enable a users account"""
        return self.update(user, {"is_disabled": False})

    def reset_password(
        self, user: User, new_password: str, reset_required: bool = False
    ) -> User:
        """Reset a users password"""
        hashed_pw, salt = hash_password(new_password)
        update: dict[str, Any] = {
            "password_hash": hashed_pw,
            "password_salt": salt,
            "reset_password": reset_required,
        }

        return self.update(user, update)
