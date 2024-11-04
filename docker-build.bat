@echo off
REM
REM Windows BATCH script to build docker container
REM
@echo on
docker rmi project03-client
docker build -t project03-client .
