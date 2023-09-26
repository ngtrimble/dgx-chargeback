# DGX-Slurm GPU Chargeback
This project provides tools to manage GPU utilization and chargeback in kube-slurm clusters.

## Related Repos
These are other Repos related to this project that contain their own documentation and tooling.
| Git Repository                                            | Description                                            |
| --------------------------------------------------------- | ------------------------------------------------------ |
| [kube-slurm](https://github.com/kalenpeterson/kube-slurm) | Tools for integrating Slurm and Kubernetes             |
| [dgx-setup](https://github.com/kalenpeterson/dgx-setup)   | Tools for configuring Nvidia DGX and Lambda Labs nodes |


## Document Index
| Document                              | Description                                                  | Version Info               |
| ------------------------------------- | ------------------------------------------------------------ | -------------------------- |
| [Chargeback Cronjob](docs/cronjob.md) | Guide to the chargeback ETL job                              | Kalen Peterson, April 2023 |
| [Chargeback API](docs/api.md)         | Guide to the Chargeback REST API Server, used to query usage | Kalen Peterson, April 2023 |


## Tool Index
| Tool               | Description                                                        | Version Info               |
| ------------------ | ------------------------------------------------------------------ | -------------------------- |
| [build](./build)   | Build scripts to generate Continer Images                          | Kalen Peterson, April 2023 |
| [deploy](./deploy) | Ansible Playbooks to deploy the Cronjob, API, and CLI to a cluster | Kalen Peterson, April 2023 |
| [src](./src)       | Python source code for chargeback                                  | Kalen Peterson, April 2023 |

