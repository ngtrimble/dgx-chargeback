# DGX-Slurm GPU Chargeback
This is intended to export GPU Utilization from Slurm, perform some processsing, and insert into a chargeback database.

## Overview
This chargeback process is written using Python 3.8, and performs the following steps.

  - Connect to the Slurm Acct DB (MySQL)
  - Connect to the Chargeback DB (MySQL)
  - Connect to a Linux host over SSH
  - Pull all completed jobs in the last 'n' days from the Slurm Acct DB
  - Parse and perform mapping of fields, including
    * Job State
    * Map user UID to name via SSH Host
  - Insert new records into the Chargeback DB
    * A query is made before insert to ensure a row with "slurm_job_id" does not already exist
  - Send and email notification with the run log file attached

### Notes
  * This script is inteded to be idemotent. It can be run multiple times and not create duplicate records
  * By default the script will pull the previous 5 days from Slurm and attempt to insert them. This helps ensure data is not lost if there is a temporary failure. They will be added on the next successful run.
  * SMTP Credentials are optional. If they are not provided, we will not attempt to authenticate to the SMTP server



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



## Simple Usage
Quick and simple ways to run this. Most useful for development and testing.

### One-shot Container
Run the chargeback process as a one-time container using podman.
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

### Run from Source (needs python3.8)
Run the python code without creating a contianer.
  * Depending on your environment, you may have missing dependencies
  * See the requiremesnt.txt and Dockerfile for dependencies
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


## Kubernetes CronJob
Now to deploy and mangae this process as a Kubernetes CronJob. More usefull for managing reliable execution over time.

### Deployment
Edit ./build/kubernetes-config.yml with your ENV vars.

  * You may omit the SMTP username and password if authentication is not required
  * The secrets must be in base64 format with no quotes. The following *nix command will convert for you.
```
echo -n 'mypassword' |base64 --wrap=0
```

Edit ./build/kubernetes-cronjob.yml with the name of the image you built, and the cron schedule you want to set.

Finally, run the deploy script to install it.
```
./build/deploy.sh
```

### Managing the CronJob
Some helpful commands to manage the Jobs

#### Check the status of the CronJob Schedule
```
kubectl get cronjob dgx-chargeback -o wide
```

#### List the current and last few runs of the job
```
kubectl get jobs -o wide
```

#### Print the logs for a specific Job run.
  * Use the above command to get the name of a job run (E.g "dgx-chargeback-xxxxxxx")
  * Run the following command with the job instance you want to see logs for
```
kubectl logs $(kubectl get pods --selector=job-name=dgx-chargeback-xxxxxxx --output=jsonpath={.items[*].metadata.name})
```

#### Run an ad-hok job anytime
  * This will execute the configured CronJob now, but will not affect future scheduled runs
  * After running an ad-hok job, you can use the above commands to monitor it
```
kubectl create job --from=cronjob/dgx-chargeback dgx-chargeback-ad-hok-$(date "+%s")
```

#### Suspend a Cronjob
  * This will prevent the CronJob from running until resumed
```
kubectl patch cronjobs dgx-chargeback -p '{"spec" : {"suspend" : true }}'
```

#### Resume a Cronjob
  * This will resume a suspended CronJob
```
kubectl patch cronjobs dgx-chargeback -p '{"spec" : {"suspend" : false }}'
```

#### Modify Job Configuration
  * Use these commands to edit the secrets, configmaps, or schedule
```
kubectl edit secret env-secret-dgx-chargeback
kubectl edit configmap env-config-dgx-chargeback
kubectl edit cronjob dgx-chargeback
```

#### Delete/Remove Job Configuration
  * Use these commands to delete the Job from the cluster
```
kubectl edit secret env-secret-dgx-chargeback
kubectl edit configmap env-config-dgx-chargeback
kubectl edit cronjob dgx-chargeback
```
