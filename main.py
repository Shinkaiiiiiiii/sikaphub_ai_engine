import hmac
import hashlib
import os
from fastapi import FastAPI, Header, HTTPException, Request, Depends
from dotenv import load_dotenv

# Import the pool connection generator and the connection type hinting
from database import get_db_connection
from mysql.connector.pooling import PooledMySQLConnection
# Import the newly created matching engine
from matching_engine import calculate_jaccard_index

# Load environment variables
load_dotenv()
HMAC_SECRET = os.getenv("HMAC_SECRET")

# Initialize the API
app = FastAPI(title="S.I.K.A.P. Hub AI Engine", version="2.0")

async def verify_hmac(request: Request, x_signature: str = Header(None)):
    """
    Cryptographic bouncer. Intercepts the request and validates the HMAC-SHA256 signature.
    """
    if not x_signature:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing Signature")

    # Read the raw byte payload of the incoming request
    body = await request.body()

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

# Inject BOTH the HMAC verification and the DB connection dependency
@app.post("/api/v1/compute-match", dependencies=[Depends(verify_hmac)])
async def compute_match(payload: dict, db: PooledMySQLConnection = Depends(get_db_connection)):
    """ 
    Fetches 3NF skill arrays from MySQL and calculates the Jaccard Index. 
    """
    job_id = payload.get("job_id")
    jobseeker_id = payload.get("jobseeker_id")
    
    if not job_id or not jobseeker_id:
        raise HTTPException(status_code=400, detail="Missing job_id or jobseeker_id")

    cursor = db.cursor(dictionary=True)
    
    try:
        # 1. Fetch Job Required Skills
        # SECURITY: Using %s prevents SQL Injection
        cursor.execute("SELECT skill_id FROM Job_Required_Skills WHERE job_id = %s", (job_id,))
        req_skills_data = cursor.fetchall()
        required_skills = [row["skill_id"] for row in req_skills_data]
        
        # 2. Fetch Job Seeker Possessed Skills
        cursor.execute("SELECT skill_id FROM JobSeeker_Skills WHERE jobseeker_id = %s", (jobseeker_id,))
        seeker_skills_data = cursor.fetchall()
        applicant_skills = [row["skill_id"] for row in seeker_skills_data]
        
        # 3. Calculate Score using the Engine
        jaccard_score = calculate_jaccard_index(required_skills, applicant_skills)
        
        # In our hybrid formula, skill match is weighted at 40% (0.40)
        weighted_skill_score = round(jaccard_score * 0.40, 4)
        
        return {
            "status": "success",
            "job_id": job_id,
            "jobseeker_id": jobseeker_id,
            "raw_jaccard_score": jaccard_score,
            "weighted_skill_score": weighted_skill_score,
            "arrays_processed": {
                "required": required_skills,
                "applicant": applicant_skills
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database execution error: {str(e)}")
    finally:
        # Always close the cursor to free up memory, even if an error occurs
        cursor.close()