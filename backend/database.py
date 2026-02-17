from sqlmodel import create_engine, Session, SQLModel
from typing import Generator

# same as alembic file
DATABASE_URL = "sqlite:///pet_chat.db"

# Is the connection to my db
engine = create_engine(DATABASE_URL, echo=True)

# allows me to make querries in code
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

#creates all tables 
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)