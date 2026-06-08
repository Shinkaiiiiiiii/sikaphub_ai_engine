import hmac
import hashlib
import os
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

# Import the newly upgraded matching engine
from matching_engine import calculate_weighted_match

# Load environment variables
load_dotenv()
HMAC_SECRET = os.getenv("HMAC_SECRET")

# Initialize the API
app = FastAPI(title="S.I.K.A.P. Hub AI Engine (Decoupled V2)", version="2.0")

# --- PYDANTIC MODELS (Defines the V2 Fat Payload Structure) ---
class JobSkill(BaseModel):
    skill_id: int
    requirement_type: str  # 'Mandatory' or 'Optional'

class SeekerSkill(BaseModel):
    skill_id: int
    proficiency_level: str

class MatchPayload(BaseModel):
    job_id: int
    jobseeker_id: int
    job_skills: List[JobSkill] = []
    seeker_skills: List[SeekerSkill] = []

async def verify_hmac(request: Request, x_signature: str = Header(None)):
    """
    Cryptographic bouncer. Validates the HMAC-SHA256 signature from PHP.
    """
    if not x_signature:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing Signature")

    # Read the raw byte payload of the incoming request
    body = await request.body()
    
    if not HMAC_SECRET:
        raise HTTPException(status_code=500, detail="Server config error: Missing HMAC_SECRET")

    # Calculate the expected signature using our shared secret
    expected_signature = hmac.new(
        key=HMAC_SECRET.encode('utf-8'),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Secure comparison (compare_digest prevents timing attacks)
    if not hmac.compare_digest(expected_signature, x_signature):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Signature")

    return True

# Inject ONLY the HMAC verification. Database dependency is completely removed!
@app.post("/api/v1/compute-match", dependencies=[Depends(verify_hmac)])
async def compute_match(payload: MatchPayload):
    """ 
    Calculates the AI match entirely in-memory using the Fat Payload from PHP.
    """
    try:
        # Calculate Score using the new Weighted Engine
        scores = calculate_weighted_match(payload.job_skills, payload.seeker_skills)
        
        return {
            "status": "success",
            "job_id": payload.job_id,
            "jobseeker_id": payload.jobseeker_id,
            "raw_jaccard_score": scores["raw_jaccard"],
            "weighted_skill_score": scores["final_weighted_score"],
            "diagnostics": {
                "mandatory_met": scores["mandatory_met"],
                "optional_met": scores["optional_met"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine execution error: {str(e)}")