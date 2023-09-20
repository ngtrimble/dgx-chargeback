#!/bin/bash
# DGX Chargeback Docker Entrypoing
#  This is a common entrypoint so that a single image can be used for both the:
#   - Nightly chargeback load
#   - Reporting REST API
#  Passing the following ARGs will start the corrosponding service
#   - chargeback
#   - api
set -e

## Chargeback Cronjob Entrypoint ##
if [ "$1" = "chargeback" ]
then
    echo "---> Starting the Chargeback Cronjob ..."
    exec /usr/local/bin/python3 main.py
fi

## Chargeback Cronjob Entrypoint ##
if [ "$1" = "api" ]
then
    echo "---> Starting the Chargeback API ..."
    exec /usr/local/bin/python3 -m uvicorn api:app --host 0.0.0.0
fi

exec "$@"
