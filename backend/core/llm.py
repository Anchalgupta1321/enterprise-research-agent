from langchain_google_genai import ChatGoogleGenerativeAI
from backend.core.config import settings

def get_llm():
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        # Raise an exception or handle the missing key
        raise ValueError("GEMINI_API_KEY is not set in the environment or .env file.")
        
    # Use gemini-flash-lite-latest which has 1500 requests/day instead of 20 requests/day
    return ChatGoogleGenerativeAI(
        model="gemini-flash-lite-latest",
        google_api_key=settings.GEMINI_API_KEY,
        max_retries=6
    )
