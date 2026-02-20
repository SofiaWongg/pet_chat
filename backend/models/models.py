# make a basic interface in python for a class with two items:

from datetime import datetime
from enum import Enum
import os
from typing import List, Optional
from sqlmodel import SQLModel, Field, Session, select
from openai import OpenAI
from pydantic import BaseModel
client = OpenAI()

Base = SQLModel


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    sender_id: int
    receiver_id: str

class ChatMessageResponse(BaseModel):
    message: str

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # messages: List[ChatMessage] - we cant store objects in a list like this in columns
    user_id: str
    pet_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    def get_messages(self, session: Session) -> List[ChatMessage]:
        return session.exec(select(ChatMessage).where((ChatMessage.conversation_id==self.id))).all()
        
    def add_message(self, message: str, sender_id: str, receiver_id: str, session: Session):
        new_message = ChatMessage(conversation_id=self.id, message=message, sender_id=sender_id, receiver_id=receiver_id)
        session.add(new_message)
        session.commit()
        session.refresh(new_message)
        return new_message
        
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

    def get_conversation_history_by_user_id_and_pet_id(self, user_id: str, session: Session) -> Conversation:
            return session.exec(select(Conversation).where((Conversation.user_id == user_id) & (Conversation.pet_id == self.id))).first()

    def chat(self, user_id: str, session: Session, message: str):
        conversation_history: Conversation = self.get_conversation_history_by_user_id_and_pet_id(user_id=user_id, session=session)
        if not conversation_history:
            new_conversation = Conversation(user_id=user_id, pet_id=self.id)
            session.add(new_conversation)
            session.commit()
            session.refresh(new_conversation)
            conversation_history = new_conversation
        conversation_history.add_message(message=message, sender_id=user_id, receiver_id=self.id, session=session)
        string_conversation_history: str = "\n".join([message.message for message in conversation_history.get_messages(session=session)])
        gpt_prompt = f"""
        You are a pet chatbot. You should pretend to be a pet {self.type} named {self.name} and should respond with a relevant message. Your personality is {self.personality}. Here is the chat history: {string_conversation_history}. Please respond to the user's latest message"""
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=gpt_prompt,
            text_format=ChatMessageResponse
        )
        new_message = response.output[0].content[0].parsed.message

        conversation_history.add_message(message=new_message, sender_id=self.id, receiver_id=user_id, session=session)

        return new_message


# Enum that relates significance level to time till expiration date in days
class SignificanceLevel(Enum):
    ONE_DAY = 1
    ONE_WEEK = 7
    ONE_MONTH = 30
    THREE_MONTHS = 90
    ONE_YEAR = 365
    FOREVER = 100000000 # forever
    

