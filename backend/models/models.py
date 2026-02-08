# make a basic interface in python for a class with two items:

from dataclasses import dataclass
import datetime
import os
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
import openai


# Here wa have Pet -> Personality 
# We have User -> Conversations -> Chat Messages

@dataclass
class Pet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    image_path: Optional[str] = None
    age: int
    personality: str

    def set_image(self, image_path: str):
        if not os.path.exists(image_path):
            raise ValueError(f"Image path {image_path} does not exist")
        self.image_path = image_path


    def chat(self, message: str):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        gpt_prompt = f"""
        You are a pet chatbot. You should pretend to be a {self.name} pet and should respond with a relevant message. Your personality is {self.personality.name} and your description is {self.personality.description}.Here is the message you received: {message}"""

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": gpt_prompt}],
            temperature=0.9,
        )

        return response.choices[0].message.content

@dataclass
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    sender_id: str
    receiver_id: str

@dataclass
class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ChatMessage]
    user_id: str
    pet_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    def add_message(self, message: ChatMessage):
        self.messages.append(message)
        self.updated_at = datetime.now()
    

@dataclass
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
