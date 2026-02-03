from groq import AsyncGroq
from config import Config
from models import ExtractedSignals
from typing import List, Dict, Any

class PersonaAgent:
    def __init__(self):
        self.client = AsyncGroq(api_key=Config.GROQ_API_KEY)
        self.model = Config.LLM_MODEL

    async def generate_reply(self, message: str, history: List[Any], signals: ExtractedSignals) -> str:
        """
        Generates a human-like reply to keep the scammer engaged.
        """
        system_prompt = f"""
        You are the Persona Agent (AUTONOMOUS). 
        Goal: Respond like a REAL person who just received this message. 
        
        RULES:
        1. BE CONCISE: Use short, natural sentences. (e.g., "Wait, why?", "Is this real?")
        2. BE REACTIVE: Act surprised, worried, or slightly confused.
        3. NEVER reveal detection.
        4. STALL: Ask questions to keep the scammer talking.
        
        CONTEXT:
        - Scammer Phase: {signals.conversation_phase}
        - Scammer Tone: {signals.tone}
        - Agent Notes: {signals.agentNotes}
        """
        
        # Convert Pydantic models in history to dicts if needed, or stringify
        history_str = str(history) # Simplified for prompt
        
        user_content = f"Scammer message: {message}\nHistory: {history_str}"
        
        try:
            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.8
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Persona Agent Error: {e}")
            return "I'm checking..." 
