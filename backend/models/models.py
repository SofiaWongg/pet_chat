# make a basic interface in python for a class with two items:

from datetime import datetime
from enum import Enum
import os
from typing import List, Literal, Optional
from sqlmodel import SQLModel, Field, Session, select
from openai import OpenAI
from pydantic import BaseModel
client = OpenAI()

Base = SQLModel


class SenderType(Enum):
    USER = "user"
    PET = "pet"

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    sender_type: SenderType

    def get_sender_id(self, session: Session) -> int:
        if self.sender_type == SenderType.USER:
            conversation = session.get(Conversation, self.conversation_id)
            return session.get(User, conversation.user_id).id
        else:
            conversation = session.get(Conversation, self.conversation_id)
            return session.get(Pet, conversation.pet_id).id    
    
    def get_receiver_id(self, session: Session) -> int:
        conversation = session.get(Conversation, self.conversation_id)
        if self.sender_type == SenderType.USER:
            return session.get(Pet, conversation.pet_id).id
        else:
            return session.get(User, conversation.user_id).id

class ChatMessageResponse(BaseModel):
    message: str

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # messages: List[ChatMessage] - we cant store objects in a list like this in columns
    user_id: int = Field(foreign_key="user.id")
    pet_id: int = Field(foreign_key="pet.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    def get_messages(self, session: Session) -> List[ChatMessage]:
        return session.exec(select(ChatMessage).where((ChatMessage.conversation_id==self.id))).all()
        
    def add_message(self, message: str, sender_type: SenderType, session: Session):
        new_message = ChatMessage(conversation_id=self.id, message=message, sender_type=sender_type)
        session.add(new_message)
        session.commit()
        session.refresh(new_message)
        return new_message

class FactType(Enum):
    # Fact type should be something that will most likely be unchanged during the pets lifespan 
    Relationship = "relationship" # ex: I have a Father named Tom, I am friends with Bob
    Like = "like" # ex: I like to play fetch, I like chocolate
    Dislike = "dislike" # ex: I dislike to play fetch, I dislike chocolate
    Location = "location" # ex: I live in a house in North Carolina
    HistoricalEvent = "historical_event" # 



class FactResponse(BaseModel):
    fact_type: FactType
    fact_text: str
    fact_subject: str
    fact_verb: str
    fact_predicate: str

class Fact(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pet_id: int = Field(foreign_key="pet.id")
    fact_type: FactType
    fact_text: str # ex: I like chocolate, I like to play fetch, I live in a house in North Carolina, I have a Father named Tom, I am friends with Bob
    fact_subject: str # ex: I, you, he, she, it, we, they
    fact_verb: str # ex: like, dislike, live, have, eat, sleep
    fact_predicate: str # ex: chocolate, fetch, North Carolina, Tom, Bob
    fact_source_user_id: int | None = None # if the fact is provided by a user it will be recorded here, else the pet has assigned it themselves
    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

    @classmethod
    def extract_facts_from_message(cls, message: str, fact_source_user_id: int | None = None) -> List[FactResponse]:
        # Call to llm to determine the number of facts in the message
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": f"You are a fact extractor. A fact is a statement about the pet or user that falls into one one of the following categories {', '.join([fact_type.value for fact_type in FactType])}. A fact should be a simple true statement. Here are some examples of facts: I like chocolate, I like to play fetch, I live in a house in North Carolina, I have a Father named Tom, I am friends with Bob. You should be able to separate each fact into the subject, verb, and predicate where the predicate does not contain the subject or verb. In the example I like to play fetch, the subject is I, the verb is like, and the predicate is to play fetch and fact type is like. You should: 1. Determine the number of facts in the message, 2. Extract the facts, 3. Return the facts in a list of dictionaries with the following keys: subject, verb, predicate, fact_type, fact_source_user_id. In cases where the fact is not clear, you should return an empty array []. Examples of statements that are not facts: 'Wow so cool!, 'What a beautiful day!', 'Are you hungry?', 'what do you think about the weather?'"},
                {"role": "user", "content": message},
            ],
            text_format=[FactResponse]
        )

        return response.output[0].content[0].parsed

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

    def get_conversation_history_by_user_id_and_pet_id(self, user_id: int, session: Session) -> Conversation:
            return session.exec(select(Conversation).where((Conversation.user_id == user_id) & (Conversation.pet_id == self.id))).first()

    def chat(self, user_id: int, session: Session, message: str):
        conversation_history: Conversation = self.get_conversation_history_by_user_id_and_pet_id(user_id=user_id, session=session)
        if not conversation_history:
            new_conversation = Conversation(user_id=user_id, pet_id=self.id)
            session.add(new_conversation)
            session.commit()
            session.refresh(new_conversation)
            conversation_history = new_conversation
        conversation_history.add_message(message=message, sender_type=SenderType.USER, session=session)
        string_conversation_history: str = "\n".join([message.message for message in conversation_history.get_messages(session=session)])

        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": f"You are a pet chatbot. You should pretend to be a pet {self.type} named {self.name} and should respond with a relevant message. Your personality is {self.personality}. Here is the chat history: {string_conversation_history}"},
                {"role": "user", "content": "Please respond to the user's latest message"},
            ],
            text_format=ChatMessageResponse
        )

        new_message = response.output[0].content[0].parsed

        conversation_history.add_message(message=new_message.message, sender_type="pet", session=session)

        return new_message.message
    

    def get_facts(self, session: Session, fact_type: FactType | None = None) -> List["Fact"]:
        # If no type is passed in we get all fact types 
        if fact_type:
            return session.exec(select(Fact).where((Fact.pet_id == self.id) & (Fact.fact_type == fact_type))).all()
        else:
            return session.exec(select(Fact).where(Fact.pet_id == self.id)).all()
