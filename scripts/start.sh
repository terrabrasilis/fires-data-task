#!/bin/bash
# The view date reference of DETER used to deter_rasterize in the SQL filter. (view_date >= '2019-08-01')
DETER_VIEW_DATE="2019-08-01"
# The data work directory.
DATA_DIR=$SHARED_DIR
export DATA_DIR
# go to the scripts directory
cd $SCRIPT_DIR
# get focuses and alerts for last month
python3 download-month-data.py

# load postgres parameters from target datadir
. ./dbconf.sh

. ./import_focuses.sh

. ./import_alerts.sh

. ./gdal_process.sh