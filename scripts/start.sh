#!/bin/bash
# to debug in localhost
# SCRIPT_DIR=`pwd`
# SHARED_DIR=$SCRIPT_DIR"/../data"
# to store run log
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
# The data work directory.
DATA_DIR=$SHARED_DIR
export DATA_DIR

# go to the scripts directory
cd $SCRIPT_DIR

# update focuses and alerts
python3 python/copy_data.py

# load postgres parameters from config file in config/pgconfig
. ./dbconf.sh
. ./gdal_process.sh >> "$DATA_DIR/gdal_process_$DATE_LOG.log" 2>&1

# update focuses classification
python3 python/classify_data.py