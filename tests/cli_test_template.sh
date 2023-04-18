#!/bin/bash

../src/main.py \
    --slurm-job-prev-day 5 \
    --slurm-assoc-backend 'slurm_acctdb' \
    --slurm-cluster-name '' \
    --slurm-db-host '' \
    --slurm-db-port 3306 \
    --slurm-db-username '' \
    --slurm-db-password '' \
    --chargeback-db-host '' \
    --chargeback-db-port 3306 \
    --chargeback-db-schema-name '' \
    --chargeback-db-table-name '' \
    --chargeback-db-username '' \
    --chargeback-db-password '' \
    --ssh-host '' \
    --ssh-port 22 \
    --ssh-username '' \
    --ssh-password '' \
    --email-smtp-host '' \
    --email-smtp-port 25 \
    --email-smtp-username '' \
    --email-smtp-password '' \
    --email-to-address 'User <user.name@example.com>' \
    --email-from-address 'DGX Chargeback <no-reply@example.com>'
