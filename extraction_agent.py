import json
import re
from models import ScamEventInput, ExtractedSignals
from config import Config
from groq import AsyncGroq

class ExtractionAgent:
    def __init__(self):
        self.client = AsyncGroq(api_key=Config.GROQ_API_KEY)

    async def extract_signals(self, event: ScamEventInput) -> ExtractedSignals:
        """
        Uses an LLM (Groq Llama-3) to extract signals.
        """
        prompt = self._construct_prompt(event)
        
        try:
            llm_response_json = await self._call_llm(prompt, event.message.text)
        except Exception as e:
            print(f"Extraction Agent LLM Error: {e}")
            # Fallback to defaults
            llm_response_json = {}

        return ExtractedSignals(
            urgency_detected=llm_response_json.get("urgency_detected", False),
            sensitive_info_request=llm_response_json.get("sensitive_info_request", False),
            suspicious_links=llm_response_json.get("intelligence", {}).get("phishingLinks", []),
            suspicious_upi=llm_response_json.get("intelligence", {}).get("upiIds", []),
            suspicious_phones=llm_response_json.get("intelligence", {}).get("phoneNumbers", []),
            sentiment=llm_response_json.get("sentiment", "neutral"),
            conversation_phase=llm_response_json.get("conversation_phase", "Unknown"),
            tone=llm_response_json.get("tone", "Unknown"),
            shouldEndConversation=llm_response_json.get("shouldEndConversation", False),
            agentNotes=llm_response_json.get("agentNotes", ""),
            intelligence=llm_response_json.get("intelligence", {})
        )
    
    def _construct_prompt(self, event: ScamEventInput) -> str:
        """Constructs the prompt for the Extraction Agent."""
        return f"""
        Analyze the following message for scam indicators. Extracted data must be precise.
        
        Message: "{event.message.text}"
        Context: Session {event.sessionId}
        
        Output JSON format:
        {{
            "urgency_detected": bool,
            "sensitive_info_request": bool,
            "intelligence": {{
                "bankAccounts": [],
                "bankNames": [],
                "upiIds": [],
                "phishingLinks": [],
                "phoneNumbers": [],
                "suspiciousKeywords": []
            }},
            "sentiment": string,
            "conversation_phase": string (e.g. "Introduction", "Grooming", "Urgency"),
            "tone": string (e.g. "Friendly", "Aggressive"),
            "shouldEndConversation": bool (Set to FALSE if the scammer is still responsive or if we can extract more info like Bank/UPI. Set to TRUE only if conversation is clearly over or circular.),
            "agentNotes": string (Brief summary of tactic)
        }}
        """

    async def _call_llm(self, system_prompt: str, user_text: str) -> dict:
        """
        Calls Groq API.
        """
        completion = await self.client.chat.completions.create(
            model=Config.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this text: {user_text}"}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        return json.loads(content)

    def compute_summary_delta(self, event: ScamEventInput, signals: ExtractedSignals) -> str:
        """Creates a structured summary line for the append-only log."""
        timestamp = event.message.timestamp.isoformat()
        sender = event.message.sender
        
        # Enriched Summary with Phase and Tone
        summary = f"[{timestamp}] {sender} ({signals.conversation_phase}|{signals.tone}): {event.message.text[:50]}..."
        
        tags = []
        if signals.urgency_detected: tags.append("URGENCY")
        if signals.sensitive_info_request: tags.append("SENSITIVE_ASK")
        if signals.suspicious_links: tags.append(f"LINKS({len(signals.suspicious_links)})")
        if signals.suspicious_upi: tags.append(f"UPI({len(signals.suspicious_upi)})")
        
        if tags:
            summary += " [" + ", ".join(tags) + "]"
            
        return summary
