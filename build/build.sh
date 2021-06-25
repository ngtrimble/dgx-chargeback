#!/bin/bash

docker build -t kalenpeterson/dgx-chargeback:latest -f Dockerfile ../

docker push kalenpeterson/dgx-chargeback:latest