#!/bin/bash
docker login --username "$DOCKER_USERNAME" --password "$DOCKER_PASSWORD"
docker push jrcichra/smartcar_test
