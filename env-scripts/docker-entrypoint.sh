#!/bin/bash
## THE ENV VARS ARE NOT READED INSIDE A SHELL SCRIPT THAT RUNS IN CRON TASKS.
## SO, WE WRITE INSIDE THE /etc/environment FILE AND READS BEFORE RUN THE SCRIPT.
echo "export SHARED_DIR=\"$SHARED_DIR\"" >> /etc/environment
echo "export DOWNLOAD_AREA=\"$DOWNLOAD_AREA\"" >> /etc/environment
echo "export SCRIPT_DIR=\"$SCRIPT_DIR\"" >> /etc/environment
echo "export TZ=\"America/Sao_Paulo\"" >> /etc/environment
echo "export GEOSERVER_BASE_URL=\"$GEOSERVER_BASE_URL\"" >> /etc/environment
echo "export GEOSERVER_BASE_PATH=\"$GEOSERVER_BASE_PATH\"" >> /etc/environment
# run cron in foreground
cron -f