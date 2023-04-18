
from fastapi import FastAPI
import common
import database
from os import environ

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/jobs/all")
async def read_jobs_all(limit: int = 10):
    
    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        environ.get("CHARGEBACK_DB_TABLE_NAME", "").strip(), environ.get("CHARGEBACK_DB_USERNAME", "").strip(),
        environ.get("CHARGEBACK_DB_PASSWORD", "").strip(), environ.get("CHARGEBACK_DB_HOST", "").strip(), 
        environ.get("CHARGEBACK_DB_PORT", "").strip(), environ.get("CHARGEBACK_DB_SCHEMA_NAME", "").strip())
    
    # Get Jobs
    jobs = chargebackDb.getJobs(limit)
    return jobs

@app.get("/jobs/users/{user_name}")
async def read_jobs_user_30days(user_name: str, months: int = 1):
    
    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        environ.get("CHARGEBACK_DB_TABLE_NAME", "").strip(), environ.get("CHARGEBACK_DB_USERNAME", "").strip(),
        environ.get("CHARGEBACK_DB_PASSWORD", "").strip(), environ.get("CHARGEBACK_DB_HOST", "").strip(), 
        environ.get("CHARGEBACK_DB_PORT", "").strip(), environ.get("CHARGEBACK_DB_SCHEMA_NAME", "").strip())
    
    # Get Jobs
    jobs = chargebackDb.getUserJobsCompletedRange(user_name, months)
    return jobs