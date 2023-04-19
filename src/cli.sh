#!/bin/bash

USER=$(whoami)
CHARGEBACK_API=http://localhost:8000

RESPONSE=$(curl -s -o - ${CHARGEBACK_API}/report/users/${USER}?months=10)

echo $RESPONSE |jq