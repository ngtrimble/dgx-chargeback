
from fastapi import FastAPI
import common
import database
from os import environ
from decimal import Decimal
from dataclasses import dataclass
from collections import Counter

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
        name='Total Jobs',
        value=None,
        description=None
    )
    completed_jobs: ReportField = ReportField(
        name='Completed Jobs',
        value=None,
        description=None
    )
    failed_jobs: ReportField = ReportField(
        name='Failed Jobs',
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
        name='Estimated Total Cost in USD',
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

    # Calculate Job Counts
    report.total_jobs.value = int(len(jobs))
    job_results = Counter(job['job_result'] for job in jobs)
    report.completed_jobs.value = int(job_results['COMPLETED'])
    report.failed_jobs.value = int(job_results['FAILED'])

    # Calulate GPU Counts
    report.total_gpus_used.value = int(sum(job['gpus_used'] for job in jobs))
    report.total_gpu_seconds.value = int(0)
    for job in jobs:
        report.total_gpu_seconds.value += int(int(job['gpus_used']) * int(job['duration_sec']))

    report.total_gpu_minutes.value = round(Decimal(report.total_gpu_seconds.value / 60), 3)
    report.total_gpu_hours.value   = round(Decimal(report.total_gpu_seconds.value / 60 / 60), 3)

    # Calulate Costs
    report.total_gpu_cost_usd.value = round(Decimal(report.total_gpu_minutes.value * Decimal(gpu_usd_cost_per_minute)), 3)

    return report

# Setup ENV
class Environment:
    
    # Chargeback DB Settings
    chargeback_db_table_name: str = environ.get("CHARGEBACK_DB_TABLE_NAME", "").strip()
    chargeback_db_username: str = environ.get("CHARGEBACK_DB_USERNAME", "").strip()
    chargeback_db_password: str = environ.get("CHARGEBACK_DB_PASSWORD", "").strip()
    chargeback_db_host: str = environ.get("CHARGEBACK_DB_HOST", "").strip()
    chargeback_db_port: int = environ.get("CHARGEBACK_DB_PORT", "").strip()
    chargeback_db_schema_name: int = environ.get("CHARGEBACK_DB_SCHEMA_NAME", "").strip()

    # Slurm DB Settings
    slurm_cluster_name: str = environ.get("SLURM_CLUSTER_NAME", "").strip()
    slurm_db_username: str = environ.get("SLURM_DB_USERNAME", "").strip()
    slurm_db_password: str = environ.get("SLURM_DB_PASSWORD", "").strip()
    slurm_db_host: str = environ.get("SLURM_DB_HOST", "").strip()
    slurm_db_port: int = environ.get("SLURM_DB_PORT", "").strip()
    slurm_db_name: str = 'slurm_acct_db'

    # Reporting Settings
    gpu_usd_cost_per_minute: Decimal = environ.get("GPU_USD_COST_PER_MINUTE", "").strip()
    min_job_duration_sec: int = 60

env = Environment()

# Build API
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello"}

@app.get("/health")
async def root():
    return {"message": "OK"}

@app.get("/report/users/{user_name}")
async def read_report_user_months(user_name: str, months: int = 1):
    
    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        env.chargeback_db_table_name,
        env.chargeback_db_username,
        env.chargeback_db_password,
        env.chargeback_db_host, 
        env.chargeback_db_port,
        env.chargeback_db_schema_name)
    
    # Get Completed Jobs for this user in the defined timerange
    jobs = chargebackDb.getUserJobsInMonthRange(user_name, months, env.min_job_duration_sec)

    # Calculate and build Report
    report = build_basic_report(jobs, env.gpu_usd_cost_per_minute, months, 'user', user_name)

    return report

@app.get("/report/groups/{user_name}")
async def read_report_group_months(user_name: str, months: int = 1):
    
    # Setup the Slurm DB
    slurmDb = database.SlurmDb(
        env.slurm_cluster_name,
        env.slurm_db_username,
        env.slurm_db_password,
        env.slurm_db_host, 
        env.slurm_db_port,
        env.slurm_db_name)
    
    # Map User to Group
    group_name = common.getUserSlurmAssoc(slurmDb.getAccountAssociations(),user_name)

    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        env.chargeback_db_table_name,
        env.chargeback_db_username,
        env.chargeback_db_password,
        env.chargeback_db_host, 
        env.chargeback_db_port,
        env.chargeback_db_schema_name)
    
    # Get Completed Jobs for this user in the defined timerange
    jobs = chargebackDb.getGroupJobsInMonthRange(group_name, months, env.min_job_duration_sec)

    # Calculate and build Report
    report = build_basic_report(jobs, env.gpu_usd_cost_per_minute, months, 'group', group_name)

    return report