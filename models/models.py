# make a basic interface in python for a class with two items:

import os


class Personality:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

class Pet:
    def __init__(self, name: str, personality: Personality, image_path: str = None):
        self.name = name
        self.personality = personality
        self.image_path = image_path
    
    def set_image(self, image_path: str):
        # Q: what is os?
        if not os.path.exists(image_path):
            raise ValueError(f"Image path {image_path} does not exist")
        self.image_path = image_path

