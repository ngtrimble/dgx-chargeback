#!/usr/bin/env python3
"""
Module Docstring
"""

__author__ = "Kalen Peterson"
__version__ = "0.1.0"
__license__ = "MIT"

from os import environ
import argparse
from logzero import logger
import database
from datetime import datetime, time, timedelta

# Slurm DB
# - Establish Connection
# - Get All Jobs completed in last n-days
# - Get all required details
#   - GPU is gres_reg or used
#   - UID is id_user
#   - SSH to node for usermap

# Chargeback DB
# - Establish Connection
# - Insert Unique records in the last n-days

# Notifications
# - Email on terminating exception
# - Email on completion

# Parsing
# - Read input from Slurm DB and parse into Chargeback format
# - Get user and group names
# - Get account name



def getDateRangeUnix(dayCount):
    thisMidnight = datetime.combine(datetime.today(), time.min)
    daysAgoMidnight = thisMidnight - timedelta(days=dayCount)
    dateRange = {
        "start": int(datetime.timestamp(daysAgoMidnight)),
        "end": int(datetime.timestamp(thisMidnight))
    }
    return dateRange


def main(args):
    """ Main entry point of the app """
    logger.info("hello world")
    logger.info(args)

    # Setup the Slurm DB
    slurmDb = database.SlurmDb(
        args.slurm_cluster_name, args.slurm_db_username,
        args.slurm_db_password, args.slurm_db_host, 
        args.slurm_db_port, 'slurm_acct_db')

    # Setup the Chargeback DB
    chargebackDb = database.ChargebackDb(
        args.chargeback_db_table_name, args.chargeback_db_username,
        args.chargeback_db_password, args.chargeback_db_host, 
        args.chargeback_db_port, args.chargeback_db_schema_name, )

    # Get Day range in UNIX Time
    dateRange = getDateRangeUnix(args.slurm_job_prev_days)
    
    # Get Jobs in range from Slrum DB
    jobs = slurmDb.getJobsRange(dateRange.get("start"), dateRange.get("end"))
    logger.info(jobs)

    # Insert Chargeback record
    #chargebackDb.addChargebackJob()




if __name__ == "__main__":
    """ This is executed when run from the command line """
    parser = argparse.ArgumentParser()

    # Misc Args
    parser.add_argument("--slurm-job-prev-days", type=int, default=environ.get("SLURM_JOB_PREV_DAYS", 3))

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

    # Email Notifications
    parser.add_argument("--email-smtp-host", default=environ.get("EMAIL_SMTP_HOST", ""))
    parser.add_argument("--email-smtp-port", default=environ.get("EMAIL_SMTP_PORT", ""))
    parser.add_argument("--email-to-address", default=environ.get("EMAIL_TO_ADDRESS", ""))
    parser.add_argument("--email-from-address", default=environ.get("EMAIL_FROM_ADDRESS", ""))

    # Optional verbosity counter (eg. -v, -vv, -vvv, etc.)
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Verbosity (-v, -vv, etc)")

    # Specify output of "--version"
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s (version {version})".format(version=__version__))

    args = parser.parse_args()
    main(args)
