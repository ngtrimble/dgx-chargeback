#!/usr/bin/python3

import getpass
import socket
import argparse
import datetime
import requests
from prettytable import PrettyTable

# Vars
api_host = socket.gethostname()
api_port = 30800
api_endpoint = 'http://{}:{}'.format(api_host, api_port)

# Get current user
username = getpass.getuser()

# Get Simple User Report
def getUserReport(api_endpoint,username):
    response = requests.get("{}/report/users/{}".format(api_endpoint,username))
    return response.json()

# Get Simple Group Report
def getGroupReport(api_endpoint,username):
    response = requests.get("{}/report/groups/{}".format(api_endpoint,username))
    return response.json()

# Print a Basic Key/Value Report in a Table
def printBasicReport(report,title):
    table = PrettyTable()
    table.field_names = [title,"Value"]
    for key, value in report.items():
        table.add_row([value['name'], value['value']])

    print(table)

def printHelp():
    help = """
    ERISXDL Chargeback Report Help

    This tool will report estimated GPU usage charged in ERISXDL for a user or group.
      - Only the user/group report for the currently logged in user are allowed.
      - Be default, the current month to date will be reported
      - The -U option is ONLY available when run as root. Non-root users may only see thier own charges.
    
    Usage: charges [-u | -g] [-U <USERNAME>]

    Options:
      -u:        Run report for jobs of current user only
      -g:        Run report for job of the current users' billing group
      -U <STR>:  Specify an alternate user to run the report as. **Only available for root user**
    
    Examples:
      Show current user's job totals/billing for the current month
        charges -u

      Show current user's billing group's totals/billing for the current month
        charges -g

      Show another user's billing totals, only when run as root
        charges -u -U username
    """
    print(help)


# Parse Args
parser = argparse.ArgumentParser()
parser.add_argument("-u", action='store_true')
parser.add_argument("-g", action='store_true')
# parser.add_argument("-d", action='store_true')
# parser.add_argument(
#         '-s',
#         type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'),
# )
# parser.add_argument(
#         '-e',
#         type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'),
# )
parser.add_argument("-U", type=str, default=None)
args = parser.parse_args()

# Check Root
if username == 'root':
    if args.U is not None:
        username = args.U
        print("You are root'. Run Report as User: '{}'".format(username))
    else:
        raise ValueError("ERROR: When running as root, you must specify a username to query with -U")

# Verify two args aren't passed
if args.u and args.g:
    raise ValueError("ERROR: You must only specify '-u' or '-g'. Not both.")

# Verify at least one arg is passed
if args.u or args.g:
    print("NOTICE: These figures are estimated based on job data as of the previous 24hours")
    print("        Final billing calculations are done by the billing team at the end of each cycle")
else:
    printHelp()

# Process arg options
if args.u:
    # Print User Report
    printBasicReport(
        getUserReport(api_endpoint,username),
        "Estimated Usage Report"
    )
elif args.g:
    # Print Group Report
    printBasicReport(
        getGroupReport(api_endpoint,username),
        "Estimated Usage Report"
    )
