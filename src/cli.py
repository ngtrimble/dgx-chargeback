#!/usr/bin/python3

import os
import argparse
import requests
from prettytable import PrettyTable

# Vars
api_endpoint = 'http://localhost:8000'

# Get current user
username = os.getlogin()

# Get Simple User Report
def getUserReport(api_endpoint,username,months):
    response = requests.get("{}/report/users/{}?months={}".format(api_endpoint,username,months))
    return response.json()

# Get Simple Group Report
def getGroupReport(api_endpoint,username,months):
    response = requests.get("{}/report/groups/{}?months={}".format(api_endpoint,username,months))
    return response.json()

# Print a Basic Key/Value Report in a Table
def printBasicReport(report,title):
    table = PrettyTable()
    table.field_names = [title,"Value"]
    for key, value in report.items():
        table.add_row([value['name'], value['value']])

    print(table)


# Parse Args
parser = argparse.ArgumentParser()
parser.add_argument("-u", action='store_true')
parser.add_argument("-g", action='store_true')
parser.add_argument("-m", type=int, default=1)
args = parser.parse_args()

if args.u:
    # Print User Report
    printBasicReport(
        getUserReport(api_endpoint,username,args.m),
        "Usage Report"
    )

if args.g:
    # Print Group Report
    printBasicReport(
        getGroupReport(api_endpoint,username,args.m),
        "Usage Report"
    )
