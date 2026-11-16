
import os
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Advanced RAG AI Assistant",
    version="1.0.0"
)

# Groq API configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = None

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "openai/gpt-oss-120b"


# Request model
class ChatRequest(BaseModel):
    prompt: str


# Home route
@app.get("/")
def home():
    return {
        "message": "Advanced RAG AI Assistant is running!"
    }


# Health check
@app.get("/health")
def health():
    return {
        "status": "running",
        "groq_configured": client is not None
    }


# Generate AI response
def generate_response(prompt: str):
    if client is None:
        raise ValueError("Groq API key is not configured.")

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a helpful AI assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=2048,
        temperature=0.7
    )

    return response.choices[0].message.content


# Chat API
@app.post("/chat")
def chat(request: ChatRequest):
    try:
        answer = generate_response(request.prompt)

        return {
            "success": True,
            "answer": answer
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
