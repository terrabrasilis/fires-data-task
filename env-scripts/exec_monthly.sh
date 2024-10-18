#!/bin/bash
source /etc/task_environment
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
${SCRIPT_DIR}"/start.sh" >> "/usr/local/data/fires_data_task_"${DATE_LOG}".log" 2>&1
