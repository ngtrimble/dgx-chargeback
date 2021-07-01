#!/usr/bin/env python3
"""
DGX Chargeback Process

Creates chargeback data for Slurm/DGX/Kubernetes clusters.

This is the main entrypoint for the process.
"""

__author__ = "Kalen Peterson"
__version__ = "0.1.0"
__license__ = "MIT"

from os import environ
import argparse
from logzero import logger
import database
from datetime import datetime, time, timedelta
import ssh
import notification


def getDateRangeUnix(dayCount):
    """
    Get start/end range in UNIX timestamps for the last n days.
    Range will always be from the previes midnight, to midnight n days ago
    """
    thisMidnight = datetime.combine(datetime.today(), time.min)
    daysAgoMidnight = thisMidnight - timedelta(days=dayCount)
    dateRange = {
        "start": int(datetime.timestamp(daysAgoMidnight)),
        "end": int(datetime.timestamp(thisMidnight))
    }
    return dateRange

def formatUnixToDateString(unixDate):
    """
    Format a UNIX time string to MySQL Datetime Format
    """
    dt = datetime.fromtimestamp(unixDate)
    dateString = dt.strftime("%Y-%m-%d %H:%M:%S")
    return dateString

def formatSlurmJobState(stateId):
    """
    Convert the Job State ID from Slurm acctdb to the friendly name
    """
    states = {
        3: 'COMPLETED',
        5: 'FAILED'
    }
    state = states.get(stateId, "UNKNOWN")
    return state

def parseSlurmJobs(jobs, sshHost):
    """
    Parse the completed slurm jobs, and prepare them for insert into chargeback DB.
    """
    chargebackRecords = []

    for job in jobs:
        
        chargebackRecord = {
            "slurm_job_name":  job["job_name"],
            "slurm_id_job":    job["id_job"],
            "time_start":      formatUnixToDateString(job["time_start"]),
            "time_end":        formatUnixToDateString(job["time_end"]),
            "duration_sec":    int(job["time_end"] - job["time_start"]),
            "cpus_req":        job["cpus_req"],
            "exit_code":       job["exit_code"],
            "user_id":         job["id_user"],
            "group_id":        job["id_group"],
            "user_name":       sshHost.mapUidtoUsername(job["id_user"]),
            "group_name":      "???",
            "nodelist":        job["nodelist"],
            "node_alloc":      job["nodes_alloc"],
            "slurm_job_state": job["state"],
            "job_result":      formatSlurmJobState(job["state"]),
            "gpus_requested":  int("0"+job["gres_req"]),
            "gpus_used":       int("0"+job["gres_used"])
        }

        chargebackRecords.append(chargebackRecord)
    
    return chargebackRecords


def main(args):
    """ Main entry point of the app """
    logger.info("Starting DGX Chargeback Run")

    # Setup the Email Connection
    emailHost = notification.Email(
        args.email_smtp_username, args.email_smtp_password,
        args.email_smtp_host, args.email_smtp_port,
        args.email_from_address, args.email_to_address)

    # Setup the Slurm DB
    slurmDb = database.SlurmDb(
        args.slurm_cluster_name, args.slurm_db_username,
        args.slurm_db_password, args.slurm_db_host, 
        args.slurm_db_port, 'slurm_acct_db')

    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        args.chargeback_db_table_name, args.chargeback_db_username,
        args.chargeback_db_password, args.chargeback_db_host, 
        args.chargeback_db_port, args.chargeback_db_schema_name)

    # Setup the SSH Connection
    sshHost = ssh.Ssh(
        args.ssh_host, args.ssh_port, args.ssh_username, args.ssh_password)

    # Get day range in UNIX Time
    dateRange = getDateRangeUnix(args.slurm_job_prev_days)
    
    # Get Jobs in range from Slurm DB
    jobs = slurmDb.getJobsRange(dateRange.get("start"), dateRange.get("end"))
    logger.info("Found '" + str(len(jobs)) + "' completed jobs to insert")

    # Format the data and get everything we need to insert into the Chargeback DB
    chargebackRecords = parseSlurmJobs(jobs, sshHost)

    # Insert Chargeback records
    for record in chargebackRecords:
        chargebackDb.addUniqueJob(record)

    # Finish up
    emailHost.sendSuccess()
    logger.info("Completed DGX Chargeback Run")



if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Misc Args
    parser.add_argument("--slurm-job-prev-days", type=int, default=environ.get("SLURM_JOB_PREV_DAYS", 5))

    # Get the Slurm Args
    parser.add_argument("--slurm-cluster-name", default=environ.get("SLURM_CLUSTER_NAME", ""))
    parser.add_argument("--slurm-db-host", default=environ.get("SLURM_DB_HOST", ""))
    parser.add_argument("--slurm-db-port", default=environ.get("SLURM_DB_PORT", ""))
    parser.add_argument("--slurm-db-username", default=environ.get("SLURM_DB_USERNAME", ""))
    parser.add_argument("--slurm-db-password", default=environ.get("SLURM_DB_PASSWORD", ""))

    # Get Chargeback DB Args
    parser.add_argument("--chargeback-db-host", default=environ.get("CHARGEBACK_DB_HOST", ""))
    parser.add_argument("--chargeback-db-port", default=environ.get("CHARGEBACK_DB_PORT", ""))
    parser.add_argument("--chargeback-db-schema-name", default=environ.get("CHARGEBACK_DB_SCHEMA_NAME", ""))
    parser.add_argument("--chargeback-db-table-name", default=environ.get("CHARGEBACK_DB_TABLE_NAME", ""))
    parser.add_argument("--chargeback-db-username", default=environ.get("CHARGEBACK_DB_USERNAME", ""))
    parser.add_argument("--chargeback-db-password", default=environ.get("CHARGEBACK_DB_PASSWORD", ""))

    # SSH Connection Details
    parser.add_argument("--ssh-host", default=environ.get("SSH_HOST", ""))
    parser.add_argument("--ssh-port", default=environ.get("SSH_PORT", ""))
    parser.add_argument("--ssh-username", default=environ.get("SSH_USERNAME", ""))
    parser.add_argument("--ssh-password", default=environ.get("SSH_PASSWORD", ""))

    # Email Notifications
    parser.add_argument("--email-smtp-host", default=environ.get("EMAIL_SMTP_HOST", ""))
    parser.add_argument("--email-smtp-port", default=environ.get("EMAIL_SMTP_PORT", ""))
    parser.add_argument("--email-smtp-username", default=environ.get("EMAIL_SMTP_USERNAME", ""))
    parser.add_argument("--email-smtp-password", default=environ.get("EMAIL_SMTP_PASSWORD", ""))
    parser.add_argument("--email-to-address", default=environ.get("EMAIL_TO_ADDRESS", ""))
    parser.add_argument("--email-from-address", default=environ.get("EMAIL_FROM_ADDRESS", ""))

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)
