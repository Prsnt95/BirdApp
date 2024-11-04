#!/bin/bash
#
# Linux/Mac BASH script to build docker container
#
docker rmi project03-client
docker build -t project03-client .
