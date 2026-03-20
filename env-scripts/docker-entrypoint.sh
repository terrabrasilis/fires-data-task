#!/bin/bash
## THE ENV VARS ARE NOT READED INSIDE A SHELL SCRIPT THAT RUNS IN CRON TASKS.
## SO, WE WRITE INSIDE THE /etc/task_environment FILE AND READS BEFORE RUN THE SCRIPT.
echo "export SHARED_DIR=\"$SHARED_DIR\"" >> /etc/task_environment
echo "export DOWNLOAD_AREA=\"$DOWNLOAD_AREA\"" >> /etc/task_environment
echo "export SCRIPT_DIR=\"$SCRIPT_DIR\"" >> /etc/task_environment
echo "export TZ=\"America/Sao_Paulo\"" >> /etc/task_environment
# Its optional, but if not defined, the default is the last prodes year.
echo "export DETER_VIEW_DATE=\"$DETER_VIEW_DATE\"" >> /etc/task_environment
# run cron in foreground
cron -f