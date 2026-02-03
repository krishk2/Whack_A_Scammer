from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class Message(BaseModel):
    sender: str
    text: str
    timestamp: datetime = datetime.now()

class ScamEventInput(BaseModel):
    sessionId: str
    message: Message
    conversationHistory: List[Message] = []
    metadata: Dict[str, Any] = {}

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = Field(default_factory=list)
    bankNames: List[str] = Field(default_factory=list)
    upiIds: List[str] = Field(default_factory=list)
    phishingLinks: List[str] = Field(default_factory=list)
    phoneNumbers: List[str] = Field(default_factory=list)
    suspiciousKeywords: List[str] = Field(default_factory=list)

class ExtractedSignals(BaseModel):
    # Keeping existing fields for compatibility, mapping new ones
    urgency_detected: bool
    sensitive_info_request: bool
    suspicious_links: List[str]
    suspicious_upi: List[str]
    suspicious_phones: List[str]
    sentiment: str
    conversation_phase: str
    tone: str
    # New integration fields
    intelligence: ExtractedIntelligence = Field(default_factory=ExtractedIntelligence)
    shouldEndConversation: bool = False
    agentNotes: str = ""

class RiskAssessment(BaseModel):
    rule_risk_score: float
    triggered_rules: List[str]

class LLMIntentScore(BaseModel):
    intent_score: float
    reasoning: str

class ScamDetectionResult(BaseModel):
    sessionId: str
    scamDetected: bool
    final_risk_score: float
    rule_risk_score: float
    llm_intent_score: float
    reasons: List[str]
    
    # New Fields for Persona/Callback
    reply: str = ""
    extractedIntelligence: Optional[ExtractedIntelligence] = None
    totalMessagesExchanged: int = 0

class AgentAPIResponse(BaseModel):
    status: str
    reply: Optional[str] = None

