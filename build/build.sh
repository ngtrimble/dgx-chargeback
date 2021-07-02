#!/bin/bash

podman build -t docker.io/kalenpeterson/dgx-chargeback:latest -f build/Dockerfile . || exit 1

podman push docker.io/kalenpeterson/dgx-chargeback:latest