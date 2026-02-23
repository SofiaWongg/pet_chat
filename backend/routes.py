from utils.db import get_all_users, get_pet_by_id, get_pet_by_name_and_type, get_user_by_id, get_user_by_name
from sqlmodel import select, Session
from fastapi import FastAPI, Depends
from pathlib import Path
import json
from models.models import Pet, User
from storage_actions import save_new_pet, load_pets
from database import get_session
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/create-pet")
async def set_new_pet(name: str, age: int, personality: str, type: str, session: Session = Depends(get_session)): 
    # session: Session = Depends(get_session) means that get_session should be called before this endpoint is run - get session typically starts your database connection
    check_if_pet_exists = get_pet_by_name_and_type(name=name, type=type, session=session)
    pet = Pet(name=name, age=age, personality=personality, type = type)
    if check_if_pet_exists:
        return {"message": "Pet already exists"}
    else:
        session.add(pet)
        session.commit()
        session.refresh(pet) # this will update the pet object with the id
    return {"message": f"Pet created successfully with id: {pet.id}"}


@app.post("/pets/{pet_id}/chat")
async def chat_with_pet(pet_id: int, user_id: int, message: str, session: Session = Depends(get_session)):
    pet: Pet = get_pet_by_id(pet_id, session=session)
    if not pet:
        return {"message": "Pet not found" }
    return {"message": pet.chat(user_id=user_id, session=session, message=message)}

@app.get("/pets/{pet_id}")
async def get_pet(pet_id: int, session: Session = Depends(get_session)):
    pet = get_pet_by_id(pet_id, session=session)
    if not pet:
        return {"message": "Pet not found" }
    return pet

@app.get("/pets")
async def get_all_pets(session: Session = Depends(get_session)):
    return session.exec(select(Pet)).all()

@app.post("/users/create")
async def create_user(user_name: str, session: Session = Depends(get_session)):
    check_if_user_exists = get_user_by_name(name=user_name, session=session)
    if check_if_user_exists:
        return {"message": "User already exists"}
    else:
        new_user = User(name=user_name)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user

@app.get("/users")
async def get_users(session: Session = Depends(get_session)):
    return get_all_users(session=session)

@app.get("/users/{user_id}")
async def get_user(user_id: int, session: Session = Depends(get_session)):
    user = get_user_by_id(id=user_id, session=session)
    if not user:
        return {"message": "User not found" }
    return user