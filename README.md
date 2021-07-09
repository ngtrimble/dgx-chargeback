# DGX-Slurm GPU Chargeback
This is intended to export GPU Utilization from Slurm, perform some processsing, and insert into a chargeback database.

## Building
Due to the requirements, it is reccomended to build the container image, and execute via container. To build...

### Clone this repo
```
git clone https://github.com/kalenpeterson/dgx-chargeback.git
```
```
cd dgx-chargeback
```

### Edit build.sh
Update build/build.sh with the desired image tag for your local repo

### Run build
Run the build. Make sure you are logged into your repo before hand.
```
podman login <your.repo>
./build/build.sh
```

Once the build completes, you can use the examples in the rest of the README


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
    -e CHARGEBACK_DB_PORT=3306 \
    -e CHARGEBACK_DB_SCHEMA_NAME='' \
    -e CHARGEBACK_DB_TABLE_NAME='' \
    -e CHARGEBACK_DB_USERNAME='' \
    -e CHARGEBACK_DB_PASSWORD='' \
    -e SSH_HOST='' \
    -e SSH_PORT=22 \
    -e SSH_USERNAME='' \
    -e SSH_PASSWORD='' \
    -e EMAIL_SMTP_HOST='' \
    -e EMAIL_SMTP_PORT=25 \
    -e EMAIL_SMTP_USERNAME='' \
    -e EMAIL_SMTP_PASSWORD='' \
    -e EMAIL_TO_ADDRESS='User <user.name@example.com>' \
    -e EMAIL_FROM_ADDRESS='DGX Chargeback <no-reply@example.com>' \
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
```