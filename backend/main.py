import json
from pathlib import Path
from fastapi import FastAPI
from models.models import Pet

app = FastAPI()
PETS_STORAGE_PATH = Path("pets.json")
PET_IMAGES_STORAGE_PATH = Path("pet_images")


def load_pets():
    if PETS_STORAGE_PATH.exists():
        with open(PETS_STORAGE_PATH, "r") as f:
            return json.load(f)
    else:
        return []

def save_new_pet(pet: Pet):
    pets = load_pets()
    pets.append(pet)
    with open(PETS_STORAGE_PATH, "w") as f:
        json.dump(pets, f)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/pets")
async def set_new_pet(pet: Pet):
    save_new_pet(pet)
    return {"message": "Pet created successfully"}
