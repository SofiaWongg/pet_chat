from fastapi import FastAPI
from pathlib import Path
import json
from models.models import Pet
from storage_actions import save_new_pet, load_pets

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/pets")
async def set_new_pet(pet: Pet):
    save_new_pet(pet)
    return {"message": "Pet created successfully"}

@app.post("/pets/{pet_id}/chat")
async def chat_with_pet(pet_id: str, message: str):
    pet = get_pet(pet_id)
    return {"message": pet.chat(message)}

@app.get("/pets/{pet_id}")
async def get_pet(pet_id: str):
    pets = load_pets()
    for pet in pets:
        if pet.id == pet_id:
            return pet
        
    return {"message": "Pet not found"}