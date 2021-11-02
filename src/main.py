#!/usr/bin/env python3
"""
DGX Chargeback Process

Creates chargeback data for Slurm/DGX/Kubernetes clusters.

This is the main entrypoint for the process.
"""

__author__ = "Kalen Peterson"
__version__ = "0.3.0"
__license__ = "MIT"

from os import environ
import sys
import argparse
import logzero
from logzero import logger
import database
from datetime import datetime, time, timedelta
import ssh
import notification
import re

"""
Define Utility functions for Main
"""
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

def formatGpuCount(gpuCount):
    """
    Convert the GPU Count from the SLurm DB, to an int
    The Slurm DB will store a string in the form "gpu:1" if a GPU was requested
    If a GPU was not requested, it will be empty
    """
    if gpuCount:
        intGpuCount = int("0"+gpuCount.split(":")[1])
        return intGpuCount
    else:
        return int(0)

def getUserGroupname(sshHost, accountName, username):
    """
    Get the GroupName for a user
    If account is not root or NULL, use that.
    If account is root or NULL, get the group list from SSH Host, and extract it
    """
    if not accountName:
        return str(accountName)
    else:
        allGroups = []
        try:
            allGroups = sshHost.mapUsernametoGroups(username)
        except Exception as err:
            logger.error(err)
            pass

        r = re.compile("^.+-G$")
        filteredGroups = list(filter(r.match, allGroups))

        if filteredGroups:
            return str(filteredGroups[0])
        else:
            logger.error("Failed to map UID: %s to Group ending in '-G'" % (username))
            return str("UNKNOWN")

def getUsername(sshHost, uid):
    """
    Get the Username for a user by UID
    """
    username = None
    try:
        username = sshHost.mapUidtoUsername(uid)
    except Exception as err:
        logger.error(err)
        pass

    if username is None:
        logger.error("Failed to map UID: %s to Username" % (uid))
        username = 'UNKOWN'

    return username

def parseSlurmJobs(jobs, sshHost):
    """
    Parse the completed slurm jobs, and prepare them for insert into chargeback DB.
    """
    chargebackRecords = []
    for job in jobs:

        time_start     = formatUnixToDateString(job["time_start"])
        time_end       = formatUnixToDateString(job["time_end"])
        duration_sec   = int(job["time_end"] - job["time_start"])
        user_name      = getUsername(sshHost,job["id_user"])
        group_name     = getUserGroupname(sshHost,job["account"],user_name)
        job_result     = formatSlurmJobState(job["state"])
        gpus_requested = formatGpuCount(job["gres_req"])
        gpus_used      = formatGpuCount(job["gres_req"])

        chargebackRecord = {
            "slurm_job_name":  job["job_name"],
            "slurm_id_job":    job["id_job"],
            "time_start":      time_start,
            "time_end":        time_end,
            "duration_sec":    duration_sec,
            "cpus_req":        job["cpus_req"],
            "exit_code":       job["exit_code"],
            "user_id":         job["id_user"],
            "group_id":        job["id_group"],
            "user_name":       user_name,
            "group_name":      group_name,
            "nodelist":        job["nodelist"],
            "node_alloc":      job["nodes_alloc"],
            "slurm_job_state": job["state"],
            "job_result":      job_result,
            "gpus_requested":  gpus_requested,
            "gpus_used":       gpus_used
        }
        chargebackRecords.append(chargebackRecord)
    
    return chargebackRecords

def main(args):
    """ Main entry point of the app """
    logzero.logfile("/tmp/chargeback.log", mode="w")
    logger.info("Starting DGX Chargeback Run")

    try:
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
        sshHost.getUsersAndGroups()

        # Get day range in UNIX Time
        dateRange = getDateRangeUnix(args.slurm_job_prev_days)
        
        # Get Jobs in range from Slurm DB
        jobs = slurmDb.getJobsRange(dateRange.get("start"), dateRange.get("end"))
        logger.info("Found '" + str(len(jobs)) + "' completed jobs to insert")

        # Format the data and get everything we need to insert into the Chargeback DB
        logger.debug("Start parsing chargeback jobs")
        chargebackRecords = parseSlurmJobs(jobs, sshHost)
        logger.debug("Completed parsing chargeback jobs")

        # Insert Chargeback records
        logger.debug("Start inserting jobs into chargeback Database")
        insertedRecords = []
        for record in chargebackRecords:
            if chargebackDb.addUniqueJob(record):
                insertedRecords.append(record)

        # Finish up
        logger.info("Completed DGX Chargeback Run")
        emailHost.sendSuccessReport(insertedRecords, "/tmp/chargeback.log")

    except Exception as err:
        logger.error('Encountered Exception: "{}"'.format(err))
        logger.error("DGX Chargeback Run Failed")
        emailHost.sendFailureReport("/tmp/chargeback.log")
        

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
