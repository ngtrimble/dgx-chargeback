#!/bin/bash

podman build -t docker.io/kalenpeterson/dgx-chargeback:latest -f build/Dockerfile .

podman push docker.io/kalenpeterson/dgx-chargeback:latest