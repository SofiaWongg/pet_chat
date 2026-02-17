# make a basic interface in python for a class with two items:

from datetime import datetime
import os
from typing import Optional
import openai
from sqlmodel import SQLModel, Field

Base = SQLModel


class Pet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) # if we don't specify the id, it will be auto-generated
    name: str
    image_path: Optional[str] = None
    age: int
    personality: str
    type: str

    def set_image(self, image_path: str):
        if not os.path.exists(image_path):
            raise ValueError(f"Image path {image_path} does not exist")
        self.image_path = image_path


    def chat(self, conversation_id: str):
        #TODO:
        #query database for converastion 
        #format conversation to go into prompt 
        conversation_history = ""
        openai.api_key = os.getenv("OPENAI_API_KEY")
        gpt_prompt = f"""
        You are a pet chatbot. You should pretend to be a {self.name} pet and should respond with a relevant message. Your personality is {self.personality}. Here is the chat history: {conversation_history}. Please respond to the usser's latest message"""
        # TODO: add response schema
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": gpt_prompt}],
            temperature=0.9,
        )

        return response.choices[0].message.content

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    sender_id: str
    receiver_id: str

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # messages: List[ChatMessage] - we cant store objects in a list like this in columns
    user_id: str
    pet_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    def add_message(self, message: ChatMessage):
        self.messages.append(message)
        self.updated_at = datetime.now()
    

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
