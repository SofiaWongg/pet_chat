pet_chat



Must do:
-pet class 
-pet should have basic attributes: name, age, personality 

-You should be able to interact with multiple pet
-You should be able to create a pet 

-there must be a UI available to interact with this pat


How would this be used:

User input's their name:
If name is found continue 

User selects a Pat to chat with 
This loads conversation history with option to:
1. Start a new chat
2. Look at an old converation
3. write a new message 

OR 
User creates a new pet
Required fields:
name
age
personality - 

Database CRUD:
# SELECT all
session.exec(select(Pet)).all()

# SELECT one by ID
session.get(Pet, pet_id)

# SELECT with WHERE
session.exec(select(Pet).where(Pet.age > 5)).all()

# INSERT
session.add(new_pet)
session.commit()

# UPDATE
pet.name = "New Name"
session.add(pet)
session.commit()

# DELETE
session.delete(pet)
session.commit()

import sqlmodel # Must add import onto migrations bc alembic does not add 
