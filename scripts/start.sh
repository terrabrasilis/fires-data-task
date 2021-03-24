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
# Includes verification of new existing and unprocessed data.
. ./deter_trigger.sh >> "$DATA_DIR/deter_trigger_$DATE_LOG.log" 2>&1
# The view date reference of DETER used to deter_rasterize in the SQL filter. (view_date >= '2019-08-01')
DETER_VIEW_DATE=$(cat $DATA_DIR/config/deter_view_date)
# load geoserver user and password from config file in config/gsconfig
. ./gsconfig.sh
# get focuses and alerts for last month
python3 download-month-data.py

# load postgres parameters from config file in config/pgconfig
. ./dbconf.sh

. ./import_focuses.sh >> "$DATA_DIR/import_focuses_$DATE_LOG.log" 2>&1

. ./import_alerts.sh >> "$DATA_DIR/import_alerts_$DATE_LOG.log" 2>&1

. ./gdal_process.sh >> "$DATA_DIR/gdal_process_$DATE_LOG.log" 2>&1