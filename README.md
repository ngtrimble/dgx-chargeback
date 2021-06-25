# DGX-Slurm GPU Chargeback
This is intended to export GPU Utilization from Slurm, perform some processsing, and insert into a chargeback database.

## Usage
### One-shot Container
```
podman run --rm \
    -e SLURM_JOB_PREV_DAYS=5 \
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
    docker.io/kalenpeterson/dgx-chargeback:latest
```

### Kubernetes CronJob
Edit build\kubernetes-config.yml with ENV vars, then run
```
build\deploy.sh
```

### Run from Source (needs python3.8)
```
cd src
pip install -r requirements.txt
python main.py \
    --slurm-job-prev-day 5 \
    --slurm-cluster-name '' \
    --slurm-db-host '' \
    --slurm-db-port '' \
    --slurm-db-username '' \
    --slurm-db-password '' \
    --chargeback-db-host '' \
    --chargeback-db-port '' \
    --chargeback-db-schema-name '' \
    --chargeback-db-table-name '' \
    --chargeback-db-username '' \
    --chargeback-db-password ''