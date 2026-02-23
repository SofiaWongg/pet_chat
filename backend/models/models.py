# make a basic interface in python for a class with two items:
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime
from enum import Enum
import os
from typing import List, Literal, Optional
from sqlmodel import SQLModel, Field, Session, select, UniqueConstraint
from openai import OpenAI
from pydantic import BaseModel
client = OpenAI()

Base = SQLModel


class ParticipantType(Enum):
    USER = "USER"
    PET = "PET"

class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id")
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    sender_type: ParticipantType

    def get_sender_id(self, session: Session) -> int:
        if self.sender_type == ParticipantType.USER:
            conversation = session.get(Conversation, self.conversation_id)
            return session.get(User, conversation.user_id).id
        else:
            conversation = session.get(Conversation, self.conversation_id)
            return session.get(Pet, conversation.pet_id).id    
    
    def get_receiver_id(self, session: Session) -> int:
        conversation = session.get(Conversation, self.conversation_id)
        if self.sender_type == ParticipantType.USER:
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
    __table_args__ = (UniqueConstraint("user_id", "pet_id", name="unique_user_pet_conversation"),)

    def get_messages(self, session: Session) -> List[ChatMessage]:
        return session.exec(select(ChatMessage).where((ChatMessage.conversation_id==self.id))).all()
        
    def add_message(self, message: str, sender_type: ParticipantType, session: Session):
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

class FactResponseList(BaseModel):
    facts: List[FactResponse]


class ContradictionResult(BaseModel):
    fact_id: Optional[int] = None


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
    def extract_facts_from_message_user(cls, message: str, user_name: str) -> List[FactResponse]:
        # Call to llm to determine the number of facts in the message
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": f"""You are a fact extractor. A fact is a statement about the pet or user that falls into one of the following categories: {', '.join([ft.value for ft in FactType])}. A fact should be a simple true statement.

This message is from a user to a pet. Facts will be stored in the pet's memory. You must normalize perspective:
- Facts about the pet: when the user says "you" they mean the pet. Rewrite in the pet's first person: subject "I", first-person verb (e.g. "was born" not "were born"), and fact_text as a first-person sentence. Example: user says "You were born in China" → subject "I", verb "was born", predicate "in China", fact_text "I was born in China".
- Facts about the user: use the name "{user_name}" as subject and keep fact_text in third person (e.g. "I like chocolate" should convert to "{user_name} likes chocolate" because "I" in the message is the user).

Extract each fact into subject, verb, and predicate (predicate does not contain subject or verb). Return a list with keys: subject, verb, predicate, fact_type, fact_text. If no clear fact, return [].
Examples of facts: I like chocolate, {user_name} likes to play fetch, I live in a house in North Carolina. Not facts: "Wow so cool!", "What a beautiful day!", "Are you hungry?"."""},
                    {"role": "user", "content": f"Extract facts if they exist from the following message: {message}"},
                ],
            text_format=FactResponseList
        )

        parsed_response: FactResponseList = response.output[0].content[0].parsed
        return parsed_response.facts

    @classmethod
    def extract_facts_from_message_pet(cls, message: str, user_name: str) -> List[FactResponse]:
        # Call to llm to determine the number of facts in the message
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": f"""You are a fact extractor. A fact is a statement about the pet or user that falls into one of the following categories: {', '.join([ft.value for ft in FactType])}. A fact should be a simple true statement.

This message is from the pet to the user (the user's name is "{user_name}"). Facts will be stored in the pet's memory. Resolve pronouns by speaker: the pet is speaking, so "I" = the pet, "You" = the user ({user_name}).
- When the pet says "You" (e.g. "You were born in China"): that is about the USER. Use subject "{user_name}", third-person fact_text. Example: "You were born in China" → subject "{user_name}", verb "was born", predicate "in China", fact_text "{user_name} was born in China".
- When the pet says "I" (e.g. "I am hungry"): that is about the PET. Use subject "I", first-person fact_text. Example: "I was born in China" → subject "I", verb "was born", predicate "in China", fact_text "I was born in China".

Extract each fact into subject, verb, and predicate (predicate does not contain subject or verb). Return a list with keys: subject, verb, predicate, fact_type, fact_text. If no clear fact, return [].
Examples of facts: I like chocolate, {user_name} likes to play fetch, I live in a house in North Carolina. Not facts: "Wow so cool!", "What a beautiful day!", "Are you hungry?"."""},
                {"role": "user", "content": f"In this message this message is from the pet to the user and they are stating {message}."},
            ],
            text_format=FactResponseList
        )

        parsed_response: FactResponseList = response.output[0].content[0].parsed
        return parsed_response.facts

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

    def get_fact_by_id(self, fact_id: int, session: Session) -> Fact:
        return session.get(Fact, fact_id)

    def add_new_fact(self, fact: Fact, session: Session):
        session.add(fact)
        session.commit()
        session.refresh(fact)
        return fact

    def is_there_existing_contradictory_fact_existing(self, fact: FactResponse, session: Session) -> Fact | None:
        # Check if fact is contradictory to any existing facts
        existing_facts: List[Fact] = self.get_facts(session=session)
        
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": f"You are a fact checker. You should check if the fact {fact.fact_text} can be added to the pet {self.name}. Here are the existing facts: {existing_facts}. If there is a contradiction between the fact and the existing facts return the contradictory fact id. If the fact can be added return None."},
            ],
            text_format=ContradictionResult
        )
        #validate that returned value is an existing fact id 
        fact_id: int | None = response.output[0].content[0].parsed.fact_id
        if fact_id is not None:
            return self.get_fact_by_id(fact_id=fact_id, session=session)
        else:
            return None

    def chat(self, user_id: int, session: Session, message: str):
        user: User = session.get(User, user_id)
        conversation_history: Conversation = self.get_conversation_history_by_user_id_and_pet_id(user_id=user_id, session=session)
        if not conversation_history:
            new_conversation = Conversation(user_id=user_id, pet_id=self.id)
            session.add(new_conversation)
            session.commit()
            session.refresh(new_conversation)
            conversation_history = new_conversation
        conversation_history.add_message(message=message, sender_type=ParticipantType.USER, session=session)
        string_conversation_history: str = "\n".join([message.message for message in conversation_history.get_messages(session=session)])

        # Determine if there is a new fact in message
        new_fact_responses: List[FactResponse] = Fact.extract_facts_from_message_user(message=message, user_name=user.name)
        print(f"[CHAT] New fact responses: {new_fact_responses}")
        # Determine if fact can be added to Pet facts

        negative_fact_context: str = "Here is some context that you should include in your response: "
        for fact_response in new_fact_responses:
            contradictory_fact: Fact | None = self.is_there_existing_contradictory_fact_existing(fact=fact_response, session=session)
            if not contradictory_fact:
                #translate response into orm model
                new_fact = Fact(pet_id=self.id, fact_type=fact_response.fact_type, fact_text=fact_response.fact_text, fact_subject=fact_response.fact_subject, fact_verb=fact_response.fact_verb, fact_predicate=fact_response.fact_predicate, fact_source_user_id=user.id)
                self.add_new_fact(fact=new_fact, session=session)
                print(f"[CHAT] Added new fact: {new_fact}")
            else:
                negative_fact_context += f"\nThe fact {fact_response.fact_text} is contradictory to the fact {contradictory_fact.fact_text}, so this fact is not a valid fact, and will not be true for this pet. Please include this insight in your response to the user. Here is an example of a response: 'Sorry, I think you are mistaken, I was born in a house in North Carolina, not in a house in Florida.' but add the pet personality to the response."
                print(f"[CHAT] Negative fact context: {negative_fact_context}")
        string_facts: str = "\n".join([fact.fact_text for fact in self.get_facts(session=session)])
        response = client.responses.parse(
            model="gpt-4o-2024-08-06",
            input=[
                {"role": "system", "content": f"You are a pet chatbot. You should pretend to be a pet {self.type} named {self.name} and should respond with a relevant message. Your personality is {self.personality}. Here are some facts about the pet: {string_facts}. Here is the chat history: {string_conversation_history}"},
                {"role": "user", "content": f"Please respond to the user's latest message. {negative_fact_context if negative_fact_context else ''}"},
            ],
            text_format=ChatMessageResponse
        )

        new_message = response.output[0].content[0].parsed
        new_fact_responses: List[FactResponse] = Fact.extract_facts_from_message_pet(message=new_message.message, user_name=user.name)
        for fact_response in new_fact_responses:
        
            contradictory_fact: Fact | None = self.is_there_existing_contradictory_fact_existing(fact=fact_response, session=session)
            if not contradictory_fact:
                #translate response into orm model
                new_fact = Fact(pet_id=self.id, fact_type=fact_response.fact_type, fact_text=fact_response.fact_text, fact_subject=fact_response.fact_subject, fact_verb=fact_response.fact_verb, fact_predicate=fact_response.fact_predicate)
                self.add_new_fact(fact=new_fact, session=session)

        conversation_history.add_message(message=new_message.message, sender_type=ParticipantType.PET, session=session)

        return new_message.message
    

    def get_facts(self, session: Session, fact_type: FactType | None = None) -> List["Fact"]:
        # If no type is passed in we get all fact types 
        if fact_type:
            return session.exec(select(Fact).where((Fact.pet_id == self.id) & (Fact.fact_type == fact_type))).all()
        else:
            return session.exec(select(Fact).where(Fact.pet_id == self.id)).all()
