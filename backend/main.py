from dotenv import load_dotenv

load_dotenv()

import json
from pathlib import Path
from fastapi import FastAPI
from models.models import Pet
import uvicorn
from routes import app


#run the app
if __name__ == "__main__":
    uvicorn.run(app, port=8001)





