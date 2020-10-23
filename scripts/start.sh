#!/bin/bash
DATA_DIR=`pwd`
DATA_DIR=$DATA_DIR"/../data"
export DATA_DIR
# get focuses and alerts for last month
python3 download-month-data.py

. ./import_focuses.sh

. ./import_alerts.sh