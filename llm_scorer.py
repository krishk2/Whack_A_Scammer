import json
from groq import AsyncGroq
from config import Config
from models import LLMIntentScore

class LLMScorer:
    def __init__(self):
        self.client = AsyncGroq(api_key=Config.GROQ_API_KEY)

    async def score_intent(self, summary_timeline: list, artifacts: dict) -> LLMIntentScore:
        """
        Real implementation using Groq LLM (Llama-3).
        """
        if not summary_timeline:
            return LLMIntentScore(intent_score=0.0, reasoning="No history to analyze.")
        
        # Construct Prompt
        # We pass the full timeline and identified artifacts
        timeline_str = "\n".join(summary_timeline)
        artifacts_str = json.dumps(artifacts, indent=2)
        
        system_prompt = """
        You are an expert Scam Detection Analyst.
        Your task is to analyze the conversation history and extracted artifacts to determine if the user is interacting with a scammer.
        
        Calculate an 'intent_score' from 0.0 (Safe) to 1.0 (Definite Scam).
        Provide a concise 'reasoning' for your score.
        
        Output MUST be valid JSON:
        {
            "intent_score": float,
            "reasoning": "string"
        }
        """
        
        user_prompt = f"""
        Analyze this session:
        
        [ARTIFACTS]
        {artifacts_str}
        
        [TIMELINE]
        {timeline_str}
        
        Generate JSON risk assessment.
        """
        
        try:
            completion = await self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            response_content = completion.choices[0].message.content
            data = json.loads(response_content)
            
            return LLMIntentScore(
                intent_score=float(data.get("intent_score", 0.0)),
                reasoning=data.get("reasoning", "Analysis failed.")
            )
            
        except Exception as e:
            print(f"LLM Error: {e}")
            return LLMIntentScore(intent_score=0.5, reasoning=f"Error calling LLM: {str(e)}")
