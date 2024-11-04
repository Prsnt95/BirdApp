@echo off
REM
REM Windows BATCH script to run docker container
REM
@echo on
docker run -it -u user -w /home/user -v .:/home/user --network="host" --rm project03-client bash
