CREATE TABLE `gpu_usage` (
	`job_id` INT(11) NOT NULL AUTO_INCREMENT COMMENT 'Chargeback Job ID',
	`slurm_job_name` CHAR(50) NOT NULL DEFAULT '' COMMENT 'Slurm Job Name' COLLATE 'latin1_swedish_ci',
	`slurm_id_job` INT(11) NOT NULL DEFAULT '0' COMMENT 'Slurm Job ID',
	`time_start` DATETIME NOT NULL COMMENT 'Datetime of Job Start',
	`time_end` DATETIME NOT NULL COMMENT 'Datetime of Job End',
	`duration_sec` INT(11) NOT NULL COMMENT 'Duration of Job in Seconds',
	`cpus_req` INT(3) NOT NULL COMMENT 'Number of CPUs Requested',
	`exit_code` INT(3) NOT NULL COMMENT 'Exit code of Job',
	`user_id` INT(20) NOT NULL COMMENT 'UNIX UID of User',
	`group_id` INT(20) NOT NULL COMMENT 'UNIX GID of User',
	`user_name` CHAR(50) NOT NULL DEFAULT '' COMMENT 'Name of User' COLLATE 'latin1_swedish_ci',
	`group_name` CHAR(50) NULL DEFAULT '' COMMENT 'Group Name of User' COLLATE 'latin1_swedish_ci',
	`nodelist` CHAR(128) NOT NULL DEFAULT '' COMMENT 'Nodes used for execution' COLLATE 'latin1_swedish_ci',
	`node_alloc` INT(2) NOT NULL DEFAULT '0' COMMENT 'Number of nodes used',
	`slurm_job_state` INT(2) NOT NULL DEFAULT '0' COMMENT 'Slurm Job State',
	`job_result` CHAR(12) NOT NULL COMMENT 'End result of job' COLLATE 'latin1_swedish_ci',
	`gpus_requested` INT(2) NULL DEFAULT '0' COMMENT 'Number of GPUs Requested',
	`gpus_used` INT(2) NULL DEFAULT '0' COMMENT 'Number of GPUs Used',
	`added` DATETIME NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Datetime when this record was added',
	`partition` CHAR(128) NOT NULL DEFAULT '' COMMENT 'Slurm Partition Name' COLLATE 'latin1_swedish_ci'
	PRIMARY KEY (`job_id`) USING BTREE
)
COLLATE='latin1_swedish_ci'
ENGINE=InnoDB
;