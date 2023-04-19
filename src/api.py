
from fastapi import FastAPI
import common
import database
from os import environ
import decimal
from decimal import Decimal

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

@app.get("/report/users/{user_name}")
async def read_report_user_30days(user_name: str, months: int = 1):
    
    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        environ.get("CHARGEBACK_DB_TABLE_NAME", "").strip(), environ.get("CHARGEBACK_DB_USERNAME", "").strip(),
        environ.get("CHARGEBACK_DB_PASSWORD", "").strip(), environ.get("CHARGEBACK_DB_HOST", "").strip(), 
        environ.get("CHARGEBACK_DB_PORT", "").strip(), environ.get("CHARGEBACK_DB_SCHEMA_NAME", "").strip())
    
    # Get Completed Jobs for this user in the defined timerange
    jobs = chargebackDb.getUserJobsCompletedRange(user_name, months)

    # Calculate report
    gpu_usd_cost_per_hour = Decimal(0.25)
    report = {}
    report['gpu_cost_per_hour'] = gpu_usd_cost_per_hour
    report['range'] = '{} months'.format(months)
    report['total_jobs'] = int(len(jobs))
    report['total_gpus_used'] = int(sum(job['gpus_used'] for job in jobs))

    report['total_gpu_seconds'] = int(0)
    for job in jobs:
        report['total_gpu_seconds'] += int(int(job['gpus_used']) * int(job['duration_sec']))

    report['total_gpu_minutes'] = round(Decimal(report['total_gpu_seconds'] / 60), 3)
    report['total_gpu_hours']   = round(Decimal(report['total_gpu_seconds'] / 60 / 60), 3)
    report['toal_gpu_cost_usd'] = round(Decimal(report['total_gpu_hours'] * gpu_usd_cost_per_hour), 3)

    return report