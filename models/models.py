# make a basic interface in python for a class with two items:

import os
from pydantic import BaseModel
from typing import Optional


class Personality(BaseModel):
    name: str
    description: str

class Pet(BaseModel):
    name: str
    personality: Personality
    image_path: Optional[str] = None

    def set_image(self, image_path: str):
        if not os.path.exists(image_path):
            raise ValueError(f"Image path {image_path} does not exist")
        self.image_path = image_path
