
from fastapi import FastAPI
import common
import database
from os import environ
import decimal
from decimal import Decimal
from dataclasses import dataclass

# Define Data Classes
@dataclass
class ReportField:
    name: str
    value: any
    description: str

@dataclass
class BasicReport:
    target_type: ReportField = ReportField(
        name='Report Target Type',
        value=None,
        description=None
    )
    target_name: ReportField = ReportField(
        name='Report Target Name',
        value=None,
        description=None
    )
    gpu_usd_cost_per_minute: ReportField = ReportField(
        name='GPU Cost/Minute in USD',
        value=None,
        description=None
    )
    range: ReportField = ReportField(
        name='Month Range',
        value=None,
        description=None
    )
    total_jobs: ReportField = ReportField(
        name='Total Completed Jobs',
        value=None,
        description=None
    )
    total_gpus_used: ReportField = ReportField(
        name='Total GPUs Used',
        value=None,
        description=None
    )
    total_gpu_seconds: ReportField = ReportField(
        name='Total GPUs Seconds Used',
        value=None,
        description=None
    )
    total_gpu_minutes: ReportField = ReportField(
        name='Total GPUs Minutes Used',
        value=None,
        description=None
    )
    total_gpu_hours: ReportField = ReportField(
        name='Total GPUs Hours Used',
        value=None,
        description=None
    )
    total_gpu_cost_usd: ReportField = ReportField(
        name='Total Cost in USD',
        value=None,
        description=None
    )

# Report Builders
def build_basic_report(jobs,gpu_usd_cost_per_minute,months,target_type,target_name):
    
    # Calculate and build Report
    report = BasicReport()
    report.target_type.value = target_type
    report.target_name.value = target_name
    report.gpu_usd_cost_per_minute.value = gpu_usd_cost_per_minute
    report.range.value = months

    report.total_jobs.value = int(len(jobs))
    report.total_gpus_used.value = int(sum(job['gpus_used'] for job in jobs))

    report.total_gpu_seconds.value = int(0)
    for job in jobs:
        report.total_gpu_seconds.value += int(int(job['gpus_used']) * int(job['duration_sec']))

    report.total_gpu_minutes.value = round(Decimal(report.total_gpu_seconds.value / 60), 3)
    report.total_gpu_hours.value   = round(Decimal(report.total_gpu_seconds.value / 60 / 60), 3)
    report.total_gpu_cost_usd.value = round(Decimal(report.total_gpu_minutes.value * gpu_usd_cost_per_minute), 3)

    return report

# Build API
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}

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
async def read_report_user_months(user_name: str, months: int = 1):
    
    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        environ.get("CHARGEBACK_DB_TABLE_NAME", "").strip(), environ.get("CHARGEBACK_DB_USERNAME", "").strip(),
        environ.get("CHARGEBACK_DB_PASSWORD", "").strip(), environ.get("CHARGEBACK_DB_HOST", "").strip(), 
        environ.get("CHARGEBACK_DB_PORT", "").strip(), environ.get("CHARGEBACK_DB_SCHEMA_NAME", "").strip())
    
    # Get Completed Jobs for this user in the defined timerange
    jobs = chargebackDb.getUserJobsCompletedRange(user_name, months)

    # Calculate and build Report
    gpu_usd_cost_per_minute = Decimal(0.008)
    report = build_basic_report(jobs, gpu_usd_cost_per_minute, months, 'user', user_name)

    return report

@app.get("/report/groups/{user_name}")
async def read_report_group_months(user_name: str, months: int = 1):
    
    # Setup the Slurm DB
    slurmDb = database.SlurmDb(
        environ.get("SLURM_CLUSTER_NAME", "").strip(), environ.get("SLURM_DB_USERNAME", "").strip(),
        environ.get("SLURM_DB_PASSWORD", "").strip(), environ.get("SLURM_DB_HOST", "").strip(), 
        environ.get("SLURM_DB_PORT", "").strip(), 'slurm_acct_db')
    
    # Map User to Group
    group_name = common.getUserSlurmAssoc(slurmDb.getAccountAssociations(),user_name)

    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        environ.get("CHARGEBACK_DB_TABLE_NAME", "").strip(), environ.get("CHARGEBACK_DB_USERNAME", "").strip(),
        environ.get("CHARGEBACK_DB_PASSWORD", "").strip(), environ.get("CHARGEBACK_DB_HOST", "").strip(), 
        environ.get("CHARGEBACK_DB_PORT", "").strip(), environ.get("CHARGEBACK_DB_SCHEMA_NAME", "").strip())
    
    # Get Completed Jobs for this user in the defined timerange
    jobs = chargebackDb.getGroupJobsCompletedRange(group_name, months)

    # Calculate and build Report
    gpu_usd_cost_per_minute = Decimal(0.008)
    report = build_basic_report(jobs, gpu_usd_cost_per_minute, months, 'group', group_name)

    return report