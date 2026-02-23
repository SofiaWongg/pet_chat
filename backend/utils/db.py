from models.models import Pet, User
from sqlmodel import Session, select


def get_pet_by_id(pet_id: int, session: Session):
    return session.get(Pet, pet_id)

def get_pet_by_name_and_type(name: str, type: str, session: Session):
    return session.exec(select(Pet).where((Pet.name == name) & (Pet.type == type))).first()

def get_user_by_name(name: str, session: Session) -> User | None:
        return session.exec(select(User).where(User.name == name)).one_or_none()

def get_user_by_id(id: int, session: Session) -> User | None:
    return session.exec(select(User).where(User.id == id)).one_or_none()

def get_all_users(session: Session) -> list[User]:
    return session.exec(select(User)).all()