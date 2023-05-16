__author__ = "Kalen Peterson"
__version__ = "0.5.0"
__license__ = "MIT"

from logzero import logger
from datetime import datetime, time, timedelta
import re

"""
Common and Utility functions
"""
def filter_list_of_dictionaries(list_of_dicts, field, value):
    filtered_list = [d for d in list_of_dicts if d.get(field) == value]
    return filtered_list

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
    REFERENCE: https://slurm-dev.schedmd.narkive.com/EI7p2GQJ/job-state-codes
    """
    states = {
        0: 'PENDING',
        1: 'RUNNING',
        2: 'SUSPENDED',
        3: 'COMPLETED',
        4: 'CANCELLED',
        5: 'FAILED',
        6: 'TIMEOUT',
        7: 'NODE_FAIL',
        8: 'PREEMPTED',
        9: 'END'
    }
    state = states.get(stateId, "UNKNOWN")
    return state

def getGpuCount(tresReq):
    """
    Extract the requested GPU Count from the tres_req field in the SlurmDb
    This field is stored in CSV format, where GPU requests are coded as '1001=n'
    An example tres_req field for a Single GPU request might look like:
        1=4,2=10240,4=1,5=4,1001=1
    Meaning, 1 GPU was requested.
    """
    if tresReq:
        tres_dict = {}
        logger.debug("tres_req field is '{}'".format(tresReq))

        try:
            for tres in tresReq.split(','):
                tres_dict[int(tres.split('=')[0])] = int(tres.split('=')[1])

            if 1001 in tres_dict:
                return tres_dict[1001]
            else:
                logger.warning("GPU Type (1001) not found in tres_req field, setting GPU count to '0'")
                return int(0)
            
        except Exception as err:
            logger.error("Failed to parse tres_req field. Look into this or users will not be charged for GPU utilization")
            logger.error(err)
            return int(0)

    else:
        logger.warning("No content found in tres_req field, setting GPU count to '0'")
        return int(0)

def getUserGroupname(sshHost, accountName, username):
    """
    Get the GroupName for a user
    If account is not root or NULL, use that.
    If account is root or NULL, get the group list from SSH Host, and extract it
    """
    if accountName:
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
        
def getUserSlurmAssoc(slurmAssocTable, username):
    """
    Get the GroupName for a user from the Slurm Assoc Table
    If we are unable to find an association, raise an error
    """
    try:
        matched_account = filter_list_of_dictionaries(slurmAssocTable, 'user', username)
    except Exception as err:
        logger.error(err)
        pass

    # If we got more than 1 result for this user, filter to only the 'default' field
    logger.debug("matched account object is '{}'".format(matched_account))
    if matched_account is not None and len(matched_account) > 1:
        logger.debug("Found '{}' matches, filtering to default".format(len(matched_account)))
        default_account = filter_list_of_dictionaries(matched_account, 'is_def', 1)
        if default_account is not None:
            matched_account = default_account
            logger.debug("default matched account object is '{}'".format(matched_account))

    if matched_account is not None:

        # Get the account name
        account = matched_account[0].get('acct', None)
        if account is not None:
            return account
        else:
            logger.error("Failed to map User '{}' to Slurm Assoc Account. Match found, but 'acct' was NULL.".format(username))
            return 'UNKNOWN'
    else:
        logger.error("Failed to map User '{}' to Slurm Assoc Account. No match found in AssocTable.".format(username))
        return 'UNKNOWN'

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

def parseSlurmJobs(jobs, sshHost, slurmAssocBackend, slurmAssocTable, slurmPartitionFilter):
    """
    Parse the completed slurm jobs, and prepare them for insert into chargeback DB.
    """
    chargebackRecords = []
    for job in jobs:

        # Skip the record if this partition is to be filtered
        if slurmPartitionFilter != '' and slurmPartitionFilter == job["partition"]:
            logger.debug("Job ID '{}' matched partition filter of '{}'. Skipping it.".format(job["id_job"],slurmPartitionFilter))
            continue

        time_start     = formatUnixToDateString(job["time_start"])
        time_end       = formatUnixToDateString(job["time_end"])
        duration_sec   = int(job["time_end"] - job["time_start"])
        user_name      = getUsername(sshHost,job["id_user"])
        job_result     = formatSlurmJobState(job["state"])
        gpus_requested = getGpuCount(job["tres_req"])
        gpus_used      = getGpuCount(job["tres_req"])

        # Route the Group mapping to the correct backend
        if slurmAssocBackend == 'etc_group':
            group_name = getUserGroupname(sshHost,job["account"],user_name)
        elif slurmAssocBackend == 'slurm_acctdb':
            group_name = getUserSlurmAssoc(slurmAssocTable,user_name)
        else:
            logger.error("slurm_assoc_backend is not set properly, this should have been caught earlier")
            group_name = 'UNKNOWN'

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
            "gpus_used":       gpus_used,
            "partition":       job["partition"]
        }
        chargebackRecords.append(chargebackRecord)
    
    return chargebackRecords