#!/bin/bash

podman run --rm \
    -e SLURM_JOB_PREV_DAYS=30 \
    -e SLURM_CLUSTER_NAME='' \
    -e SLURM_DB_HOST='' \
    -e SLURM_DB_PORT=3306 \
    -e SLURM_DB_USERNAME='' \
    -e SLURM_DB_PASSWORD='' \
    -e CHARGEBACK_DB_HOST='' \
    -e CHARGEBACK_DB_PORT=3316 \
    -e CHARGEBACK_DB_SCHEMA_NAME='' \
    -e CHARGEBACK_DB_TABLE_NAME='' \
    -e CHARGEBACK_DB_USERNAME='' \
    -e CHARGEBACK_DB_PASSWORD='' \
    -e SSH_HOST='' \
    -e SSH_PORT=22 \
    -e SSH_USERNAME='' \
    -e SSH_PASSWORD='' \
    -e EMAIL_SMTP_HOST='' \
    -e EMAIL_SMTP_PORT='' \
    -e EMAIL_TO_ADDRESS='' \
    -e EMAIL_FROM_ADDRESS='' \
    docker.io/kalenpeterson/dgx-chargeback:latest

