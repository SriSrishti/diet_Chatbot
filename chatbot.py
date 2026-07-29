
# Coding

import os

from datetime import datetime, timezone
import certifi
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

groq_api_key = os.getenv("GROQ_API_Key")
mongo_uri = os.getenv("MONGODB_URI")

# print(groq_api_key)
# print(mongo_uri)

# client = MongoClient("mongodb+srv://srishtikumari325_db_user:Yyt70Qv2Ud7VnmRH@cluster0.szwbpb6.mongodb.net/?appName=Cluster0")
client = MongoClient(mongo_uri, tlsCAFile=certifi.where())

db = client["Chatbot"]
collection = db["users"]

app = FastAPI()

class ChatRequest(BaseModel):
    user_id: str
    question: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an Fitness coach. Guide me related to fitness.",
        ),
        ("placeholder","{history}"),
        ("user", "{question}"),
    ]
)

llm = ChatGroq(api_key= groq_api_key, model = "openai/gpt-oss-20b")
chain = prompt | llm



def get_history(user_id):
    chats =  collection.find({"user_id": user_id}).sort("timestamp", 1)
    history = []

    for chat in chats:
      history.append(f"{chat['role']}: {chat['message']}")

    return history

@app.get("/") #root route

def home():
    return {"message": "Welcome to the Diet Specialist Chatbot API!"}

@ app.post("/chat")

def chat(request: ChatRequest):
     history = get_history(request.user_id)
     response = chain.invoke({"history":history,"question": request.question})
     collection.insert_one(
        {
            "user_id": request.user_id,
            "role": "user",
            "message": request.question,
            "timestamp": datetime.now(timezone.utc),
        }
    )
      # Save assistant response to MongoDB
     collection.insert_one(
        {
            "user_id": request.user_id,
            "role": "assistant",
            "message": response.content,
            "timestamp": datetime.now(timezone.utc),
        }
    )

     return {"response" : response.content}



