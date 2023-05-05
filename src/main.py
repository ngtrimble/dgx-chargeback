#!/usr/bin/env python3
"""
DGX Chargeback Process

Creates chargeback data for Slurm/DGX/Kubernetes clusters.

This is the main entrypoint for the process.
"""

__author__ = "Kalen Peterson"
__version__ = "0.5.0"
__license__ = "MIT"

from os import environ
import argparse
import logzero
from logzero import logger
import common
import database
import ssh
import notification

def main(args):
    """ Main entry point of the app """
    logzero.loglevel(logzero.DEBUG)
    logzero.logfile("/tmp/chargeback.log", mode="w", loglevel=logzero.DEBUG)
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
        
        # Setup the Account Associations backend
        slurmAssocBackend = args.slurm_assoc_backend
        logger.info("Account association backend set to {}".format(slurmAssocBackend))
        if slurmAssocBackend == 'slurm_acctdb':
            slurmAssocTable = slurmDb.getAccountAssociations()
            logger.debug("Retrieved slurmAssocTable with {} unique entries".format(len(slurmAssocTable)))
        elif slurmAssocBackend == 'etc_group':
            slurmAssocTable = None
        else:
            raise Exception("slurm_assoc_backend is undefined or invalid. valid values are ['etc_group','slurm_acctdb']")
        
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
        logger.info("Looking for completed Slurm jobs in the past '{}' days".format(args.slurm_job_prev_days))
        dateRange = common.getDateRangeUnix(args.slurm_job_prev_days)
        logger.debug("Calulated Date-Range in unixtime is '{}' to '{}'".format(dateRange.get("start"), dateRange.get("end")))
        
        # Get Jobs in range from Slurm DB
        logger.debug("Collecting Jobs from SlurmDb in daterange")
        jobs = slurmDb.getJobsRange(dateRange.get("start"), dateRange.get("end"))
        logger.info("Found '" + str(len(jobs)) + "' completed jobs to insert")

        # Format the data and get everything we need to insert into the Chargeback DB
        logger.debug("Start parsing chargeback jobs")
        chargebackRecords = common.parseSlurmJobs(jobs, sshHost, slurmAssocBackend, slurmAssocTable, args.slurm_partition_filter)
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
    parser.add_argument("--slurm-job-prev-days", type=int, default=environ.get("SLURM_JOB_PREV_DAYS", 5).strip())

    # Define the Account association backend
    #  Can be "etc_group" or "slurm_acctdb"
    parser.add_argument("--slurm-assoc-backend", default=environ.get("SLURM_ASSOC_BACKEND", "").strip())

    # A filter to exclude the name of (1) partition
    #  only one name is supported for now, and must be an exact match
    #  added to support filtering out jobs from the basic partition
    #  if unset or empty, will be ignored
    parser.add_argument("--slurm-partition-filter", default=environ.get("SLURM_PARTITION_FILTER", "").strip())

    # Get the Slurm Args
    parser.add_argument("--slurm-cluster-name", default=environ.get("SLURM_CLUSTER_NAME", "").strip())
    parser.add_argument("--slurm-db-host", default=environ.get("SLURM_DB_HOST", "").strip())
    parser.add_argument("--slurm-db-port", default=environ.get("SLURM_DB_PORT", "").strip())
    parser.add_argument("--slurm-db-username", default=environ.get("SLURM_DB_USERNAME", "").strip())
    parser.add_argument("--slurm-db-password", default=environ.get("SLURM_DB_PASSWORD", "").strip())

    # Get Chargeback DB Args
    parser.add_argument("--chargeback-db-host", default=environ.get("CHARGEBACK_DB_HOST", "").strip())
    parser.add_argument("--chargeback-db-port", default=environ.get("CHARGEBACK_DB_PORT", "").strip())
    parser.add_argument("--chargeback-db-schema-name", default=environ.get("CHARGEBACK_DB_SCHEMA_NAME", "").strip())
    parser.add_argument("--chargeback-db-table-name", default=environ.get("CHARGEBACK_DB_TABLE_NAME", "").strip())
    parser.add_argument("--chargeback-db-username", default=environ.get("CHARGEBACK_DB_USERNAME", "").strip())
    parser.add_argument("--chargeback-db-password", default=environ.get("CHARGEBACK_DB_PASSWORD", "").strip())

    # SSH Connection Details
    parser.add_argument("--ssh-host", default=environ.get("SSH_HOST", "").strip())
    parser.add_argument("--ssh-port", default=environ.get("SSH_PORT", "").strip())
    parser.add_argument("--ssh-username", default=environ.get("SSH_USERNAME", "").strip())
    parser.add_argument("--ssh-password", default=environ.get("SSH_PASSWORD", "").strip())
    parser.add_argument("--ssh-file-cleanup", default=environ.get("SSH_FILE_CLEANUP", "").strip())

    # Email Notifications
    parser.add_argument("--email-smtp-host", default=environ.get("EMAIL_SMTP_HOST", "").strip())
    parser.add_argument("--email-smtp-port", default=environ.get("EMAIL_SMTP_PORT", "").strip())
    parser.add_argument("--email-smtp-username", default=environ.get("EMAIL_SMTP_USERNAME", "").strip())
    parser.add_argument("--email-smtp-password", default=environ.get("EMAIL_SMTP_PASSWORD", "").strip())
    parser.add_argument("--email-to-address", default=environ.get("EMAIL_TO_ADDRESS", "").strip())
    parser.add_argument("--email-from-address", default=environ.get("EMAIL_FROM_ADDRESS", "").strip())

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)
