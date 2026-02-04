from fastapi import FastAPI, HTTPException, Security, Header,Request
from fastapi.security import APIKeyHeader
from models import ScamEventInput, AgentAPIResponse
from config import Config
from extraction_agent import ExtractionAgent
from risk_engine import RiskEngine
from memory_store import MemoryStore
from llm_scorer import LLMScorer
from persona_agent import PersonaAgent
import httpx
import os
import asyncio
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="Scam Detection Agent")

# Security Scheme
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)




# Add this block to your main FastAPI application file (main.py or app.py)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """
    Ensures all standard HTTP errors (403, 404, 500) return a JSON body 
    that matches the required error format from the problem statement.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail # Uses the error message from the exception (e.g., "Could not validate credentials")
        },
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """
    Catches all UNHANDLED exceptions (Python crashes) and returns a 500 
    JSON error. This is the single most important fix for "Expecting value".
    """
    # Log the full traceback to your console for debugging
    import traceback
    print("FATAL UNHANDLED EXCEPTION:")
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error: An unhandled exception occurred during processing."
        },
    )


async def get_api_key(api_key: str = Security(api_key_header)):
    EXPECTED_KEY = os.getenv("SERVICE_API_KEY")
    if not EXPECTED_KEY:
        # Fallback or Error. For now, let's warn.
        print("WARNING: SERVICE_API_KEY not set in .env")
        raise HTTPException(status_code=500, detail="Server Configuration Error")
        
    if api_key != EXPECTED_KEY:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials"
        )
    return api_key

# Initialize Components
memory_store = MemoryStore()
extraction_agent = ExtractionAgent()
risk_engine = RiskEngine()
llm_scorer = LLMScorer()
persona_agent = PersonaAgent()

@app.post("/detect", response_model=AgentAPIResponse)
async def detect_scam(event: ScamEventInput,  request: Request, api_key: str = Security(get_api_key)):
    # logging block
    print("\n" + "="*70)
    print(f"DEBUG: RECEIVED NEW REQUEST at {request.url}")

    # 1. Log all Headers (Crucial for Content-Type and x-api-key check)
    print("DEBUG: RECEIVED HEADERS:")
    for key, value in request.headers.items():
        print(f"  {key}: {value}")
    
    # 2. Log Raw Body (The absolute best way to catch non-JSON data)
    # WARNING: To get the raw body, you must call .body() BEFORE the Pydantic 
    # model (ScamEventInput) attempts to access it. Fortunately, FastAPI will
    # handle the body access even with the Pydantic dependency.
    try:
        raw_body = await request.body()
        # Decode body to see it as a string, including any leading/trailing garbage
        print("DEBUG: RAW REQUEST BODY:")
        print(raw_body.decode('utf-8'))
    except Exception as e:
        print(f"DEBUG: Could not read raw body: {e}")
    
    print("="*70 + "\n")
    
    # Step 0: Increment Message Count
    total_msgs = await memory_store.increment_message_count(event.sessionId)

    # Step 1: Extract Signals & Compute Summary Delta
    signals = await extraction_agent.extract_signals(event)
    summary_delta = extraction_agent.compute_summary_delta(event, signals)
    
    # Check if this session is already a confirmed scam
    is_already_scam = await memory_store.is_session_scam(event.sessionId)
    
    # Defaults
    scam_detected = False
    final_risk = 0.0
    rule_risk_score = 0.0
    llm_intent_score = 0.0
    reasons = []

    if is_already_scam:
        # SHORT-CIRCUIT: Skip Detection Agents
        print(f"Session {event.sessionId} is ALREADY confirmed scam. Skipping detection logic.")
        scam_detected = True
        final_risk = 1.0
        
        # We still need to update memory with new artifacts found by Extraction Agent
        new_artifacts = signals.intelligence.model_dump(exclude_none=True)
        # Update legacy keys for safety
        if signals.suspicious_links: new_artifacts["suspicious_links"] = signals.suspicious_links
        if signals.suspicious_upi: new_artifacts["upi_ids"] = signals.suspicious_upi
        if signals.suspicious_phones: new_artifacts["phone_numbers"] = signals.suspicious_phones
        
        # Async update memory & summary (we still want the summary for context)
        await asyncio.gather(
            memory_store.update_artifact_memory(event.sessionId, new_artifacts),
            memory_store.append_summary(event.sessionId, summary_delta)
        )
        summary_timeline = await memory_store.get_summary(event.sessionId)
        
    else:
        # NORMAL FLOW: Execute Detection Stack
        
        # Step 2: Parallel Execution
        # Update Artifact Memory (Intelligence Accumulation)
        # Store all ExtractedIntelligence fields
        new_artifacts = signals.intelligence.model_dump(exclude_none=True)
        # Also map legacy keys if needed for internal scoring (though we can switch scoring to use new keys too)
        if signals.suspicious_links: new_artifacts["suspicious_links"] = signals.suspicious_links
        if signals.suspicious_upi: new_artifacts["upi_ids"] = signals.suspicious_upi
        if signals.suspicious_phones: new_artifacts["phone_numbers"] = signals.suspicious_phones
        
        risk_task = asyncio.create_task(async_compute_rule_risk(signals))
        mem_update_task = asyncio.create_task(memory_store.update_artifact_memory(event.sessionId, new_artifacts))
        summary_update_task = asyncio.create_task(memory_store.append_summary(event.sessionId, summary_delta))
        
        rule_risk_assessment, _, _ = await asyncio.gather(risk_task, mem_update_task, summary_update_task)
        
        # Step 3: Prepare Data for LLM
        summary_timeline = await memory_store.get_summary(event.sessionId)
        known_artifacts = await memory_store.get_artifacts(event.sessionId)
        
        # Step 4: LLM Intent Scoring
        llm_result = await llm_scorer.score_intent(summary_timeline, known_artifacts)
        
        # Step 5: Risk Fusion Gate
        # final_risk = α · rule_risk + β · llm_intent
        final_risk = (Config.ALPHA * rule_risk_assessment.rule_risk_score) + \
                     (Config.BETA * llm_result.intent_score)
        
        scam_detected = final_risk >= Config.SCAM_THRESHOLD
        
        rule_risk_score = rule_risk_assessment.rule_risk_score
        llm_intent_score = llm_result.intent_score
        reasons = rule_risk_assessment.triggered_rules + [llm_result.reasoning]
        
        # Mark as scam if newly detected
        if scam_detected:
            await memory_store.mark_session_as_scam(event.sessionId)
    
    # Step 6: Persona Agent (Activation) & Lifecycle Management
    reply = None
    if scam_detected:
        # Autonomous Reply Generation
        reply = await persona_agent.generate_reply(event.message.text, summary_timeline, signals)
        
        # Check for End of Conversation
        if signals.shouldEndConversation:
            # Trigger Final Result Callback with ACCUMULATED Intelligence
            # We must fetch the latest state from memory (which includes what we just added)
            final_artifacts = await memory_store.get_artifacts(event.sessionId)
            await trigger_final_callback(event.sessionId, total_msgs, signals, final_artifacts)

    # --- Logging ---
    print("\n" + "="*50)
    print(f"Session: {event.sessionId}")
    print(f"Message: {event.message.text}")
    print(f"Phase: {signals.conversation_phase} | Tone: {signals.tone}")
    print(f"Signals: Urgency={signals.urgency_detected}, Sensitive={signals.sensitive_info_request}")
    print(f"Intelligence: {signals.intelligence}")
    print("-" * 20)
    
    if is_already_scam:
        print("Verdict: SCAM DETECTED (Already Confirmed - Detection Skipped)")
    else:
        print(f"Rule: {rule_risk_score:.2f} | LLM: {llm_intent_score:.2f} | Final: {final_risk:.4f}")
        print(f"Verdict: {'SCAM DETECTED' if scam_detected else 'SAFE'}")
    if reply:
        print(f"Persona Reply: {reply}")
    print("="*50 + "\n")
    # ----------------
    
    return AgentAPIResponse(
        status="success",
        reply=reply
    )

async def trigger_final_callback(session_id: str, total_msgs: int, signals, final_artifacts: dict):
    """
    Sends the mandatory final result to the platform.
    """
    url = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
    
    # Map flat artifacts dict to structured ExtractedIntelligence format
    # Redis stores sets as lists, we need to ensure keys match ExtractedIntelligence fields
    intel_payload = {
        "bankAccounts": final_artifacts.get("bankAccounts", []),
        "bankNames": final_artifacts.get("bankNames", []),
        "upiIds": final_artifacts.get("upiIds", []) + final_artifacts.get("upi_ids", []), # Handle both keys
        "phishingLinks": final_artifacts.get("phishingLinks", []) + final_artifacts.get("suspicious_links", []),
        "phoneNumbers": final_artifacts.get("phoneNumbers", []) + final_artifacts.get("phone_numbers", []),
        "suspiciousKeywords": final_artifacts.get("suspiciousKeywords", [])
    }
    
    # Deduplicate lists
    for k in intel_payload:
        intel_payload[k] = list(set(intel_payload[k]))

    payload = {
        "sessionId": session_id,
        "scamDetected": True,
        "totalMessagesExchanged": total_msgs,
        "extractedIntelligence": intel_payload,
        "agentNotes": signals.agentNotes
    }
    
    print(f"[CALLBACK] Sending Final Result to {url}...")
    try:
        async with httpx.AsyncClient() as client:
           print(f"[CALLBACK] Payload: {payload}")
           # await client.post(url, json=payload) 
    except Exception as e:
        print(f"[CALLBACK] Failed: {e}")


async def async_compute_rule_risk(signals):
    """Wrapper to make sync function awaitable if needed, or just run it."""
    return risk_engine.compute_risk(signals)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
