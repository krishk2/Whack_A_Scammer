import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "redis-16983.c330.asia-south1-1.gce.cloud.redislabs.com")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 16983))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "vH53KZewY9BAqy2oA1wQFXFpUlPg8ZTs")

    # Risk Fusion Weights (Must sum to 1.0)
    # Prioritize LLM as it understands context/intent better than regex
    ALPHA = 0.2  # Rule-based weight
    BETA = 0.8   # LLM-based weight
    SCAM_THRESHOLD = 0.75

    # LLM Settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
    LLM_MODEL = "llama-3.3-70b-versatile"
