from typing import Optional

from sqlalchemy.orm import Session

from adapters.orm.models import UserModel
from domain.entities import User as DomainUser
from domain.repositories import UserRepository


class UserRepositorySQLAlchemy(UserRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, m: UserModel) -> DomainUser:
        return DomainUser(id=m.id, username=m.username, email=m.email, created_at=m.created_at)

    def add(self, user: DomainUser) -> DomainUser:
        model = UserModel(username=user.username, email=user.email)
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, user_id: int) -> Optional[DomainUser]:
        m = self.session.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(m) if m else None

    def get_by_username(self, username: str) -> Optional[DomainUser]:
        m = self.session.query(UserModel).filter(UserModel.username == username).first()
        return self._to_domain(m) if m else None
