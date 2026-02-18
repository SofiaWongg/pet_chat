from pathlib import Path
import json
import select
from models.models import Conversation, Pet
from sqlmodel import Session

PETS_STORAGE_PATH = Path("pets.json")
PET_IMAGES_STORAGE_PATH = Path("pet_images")

def save_new_pet(pet: Pet):
    pets = load_pets()
    pets.append(pet)
    with open(PETS_STORAGE_PATH, "w") as f:
        json.dump(pets, f)

def load_pets():
    if PETS_STORAGE_PATH.exists():
        with open(PETS_STORAGE_PATH, "r") as f:
            return json.load(f)
    else:
        return []

def get_conversation_by_user_id_and_pet_id(user_id: str, pet_id: str, session: Session) -> Conversation:
    return session.exec(select(Conversation).where((Conversation.user_id == user_id) & (Conversation.pet_id == pet_id))).first()
